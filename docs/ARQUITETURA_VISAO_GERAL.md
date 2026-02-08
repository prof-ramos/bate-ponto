# Visão Geral de Alto Nível - Bate-Ponto Discord Bot

**Versão**: 1.0
**Data**: 08/02/2026
**Autor**: Architect-Writer-1 (Swarm Agent)
**Epic**: Documentação de Arquitetura
**Relacionado**: PRD.md (seções 1-4), ARQUITETURA.md, FASE1_RELATARIO.md

---

## 1. Propósito e Escopo do Sistema

### 1.1 Objetivo Principal

Conforme definido no **PRD.md (Seção 1)**, o **Bate-Ponto** é um bot Discord para **rastreamento e ranking de atividade** de membros em servidores, com foco principal em **tempo de participação com câmera ligada** em canais de voz.

**Propósito Específico**:
- **Gamificar** a participação ativa através de métricas visíveis de engajamento
- **Incentivar** o uso de câmera em reuniões/chamadas através de competição saudável
- **Rastrear** automaticamente tempo de câmera sem intervenção manual
- **Persistir** dados para consulta histórica e análise de tendências

### 1.2 Escopo Atual (Fase 1)

**Funcionalidades Implementadas** ✅:
- ✅ **RF01**: Rastreamento automático de tempo com câmera ligada
- ✅ **RF04**: Comando `!rankingvideo` (top 10 usuários)
- ✅ **RF06**: Persistência em JSON (`video_ranking.json`)
- ✅ **RF07**: Gestão de sessões ativas com locks (`VideoSessionManager`)

**Funcionalidades Futuras (Fases 2-3)** ⬜:
- ⬜ **RF02**: Rastreamento de tempo em voz (com/sem câmera)
- ⬜ **RF03**: Rastreamento de mensagens enviadas
- ⬜ **RF05**: Comando `!meustats` (estatísticas individuais)
- ⬜ Persistência de sessões ativas em restart
- ⬜ Sistema de backup automático
- ⬜ Comando admin para reset de dados

### 1.3 Público-Alvo e Limites

**Público-Alvo** (PRD.md Seção 1.3):
- Servidores Discord com **até 50 membros ativos** (escalável até ~100)
- Comunidades que valorizam participação visual em chamadas
- Equipes que desejam gamificar engajamento

**Limites do MVP**:
- Escala limitada a ~100 usuários (JSON como persistência)
- Single-guild (um servidor Discord por instância)
- Sem persistência de sessões ativas em restart
- Sem suporte a multi-guild nativo

---

## 2. Stack Tecnológico

### 2.1 Visão Geral

| Camada | Tecnologia | Versão | Justificativa |
|--------|-----------|--------|---------------|
| **Linguagem** | Python | 3.10+ | Type hints (RNF10), async/await nativo, ecossistema rico |
| **Discord SDK** | discord.py | 2.3+ | Biblioteca mais madura para Discord em Python |
| **Persistência** | JSON | (builtin) | Simplicidade para MVP, legibilidade (RNF12), migração facilitada |
| **Gestão de Tempo** | datetime | (builtin) | Cálculo preciso de durações de sessão |
| **Concorrência** | asyncio | (builtin) | Locks, paralelização de fetches, I/O eficiente |
| **Testes** | pytest | 7.0+ | Suíte de testes automatizados (82% cobertura) |
| **Deploy** | Docker/VPS | Ubuntu 22.04+ | Containerização ou VM para produção |

### 2.2 Rationale das Decisões Tecnológicas

**Por que Python?**
- **Type Hints**: Código 100% tipado (RNF10) facilita manutenção
- **Async/Await**: Performance superior para I/O bound (API calls, file operations)
- **Ecossistema**: Bibliotecas maduras para Discord, testes, deploy
- **Legibilidade**: Código limpo e bem documentado

**Por que discord.py?**
- Biblioteca **mais madura** para Discord em Python
- Suporte completo a **Intents** necessários (voice_states, members)
- Comunidade ativa e documentação extensa
- Compatível com async/await nativo

**Por que JSON (MVP)?**
- **Simplicidade**: Sem necessidade de setup de banco de dados
- **Legibilidade**: Arquivo legível (indent=2, RNF12)
- **Portabilidade**: Fácil migração para SQLite/PostgreSQL
- **Adequado ao Escopo**: Performance OK para 50-100 usuários

**Por que Asyncio?**
- **Paralelização**: `asyncio.gather()` reduz tempo de 2-5s para 200-500ms
- **Locks**: `asyncio.Lock()` previne race conditions em sessões
- **I/O Bound**: Discord API e file operations são I/O bound
- **Escalabilidade**: Prepara para crescimento futuro

### 2.3 Dependências Principais

**requirements.txt**:
```txt
discord.py>=2.3.0    # Discord API wrapper
python-dotenv>=1.0.0 # Gestão de variáveis de ambiente
pytest>=7.0.0        # Testes automatizados
pytest-asyncio>=0.21 # Suporte a async em testes
pytest-cov>=4.0.0    # Cobertura de testes
```

---

## 3. Arquitetura em Camadas

O sistema segue uma arquitetura em **4 camadas** com separação clara de responsabilidades:

### 3.1 Diagrama de Camadas

```
┌─────────────────────────────────────────────────────────────┐
│              CAMADA DE APRESENTAÇÃO (Orquestração)         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  bot.py (Facade / Orquestrador)                     │  │
│  │  - Inicialização do bot                               │  │
│  │  - Registro de events/commands                        │  │
│  │  - Tratamento de erros globais                        │  │
│  │  - Configuração de Intents                            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  CAMADA DE APLICAÇÃO (Lógica)               │
│  ┌──────────────────────┐  ┌────────────────────────────┐  │
│  │  commands.py         │  │  events.py                 │  │
│  │  (Command Handlers)  │  │  (Event Handlers)          │  │
│  │                       │  │                            │  │
│  │  - ranking_video()   │  │  - on_voice_state_update() │  │
│  │  - Formatação Embed  │  │  - VideoSessionManager     │  │
│  │  - Lazy Loading      │  │  - Session Locks           │  │
│  └──────────────────────┘  └────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 CAMADA DE DOMÍNIO (Modelo)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  utils.py                                             │  │
│  │  (Funções Auxiliares)                                 │  │
│  │                                                        │  │
│  │  - format_seconds_to_time()  (Formatação)            │  │
│  │  - fetch_user()              (Paralelização)         │  │
│  │  - validate_user_id()        (Validação)             │  │
│  │  - truncate_string()         (Utilidades)            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              CAMADA DE PERSISTÊNCIA (Dados)                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  database.py                                          │  │
│  │  (Active Record Simplificado)                         │  │
│  │                                                        │  │
│  │  - load_data()              (Read)                    │  │
│  │  - save_data()              (Write)                   │  │
│  │  - update_video_time()      (Update)                  │  │
│  │                                                        │  │
│  │  video_ranking.json (Arquivo Físico)                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Responsabilidades por Camada

#### Camada de Apresentação (bot.py)
- **Orquestração**: Inicializa e configura o bot
- **Registro**: Registra event handlers e command handlers
- **Erros**: Tratamento global de erros
- **Interface**: Fornece interface unificada (Facade Pattern)

#### Camada de Aplicação (commands.py, events.py)
- **Lógica de Negócio**: Implementa comandos e eventos
- **Formatação**: Prepara dados para exibição (Embeds)
- **Gerenciamento de Estado**: Controla sessões ativas
- **Paralelização**: Otimiza performance com async

#### Camada de Domínio (utils.py)
- **Modelo de Dados**: Formatação e validação
- **Regras de Domínio**: Conversão de tempo, validação de IDs
- **Utilidades**: Funções reutilizáveis

#### Camada de Persistência (database.py)
- **CRUD**: Create, Read, Update, Delete
- **Serialização**: Converte objetos para JSON
- **Consistência**: Garante integridade dos dados

---

## 4. Padrões Arquiteturais Aplicados

### 4.1 Active Record (Simplificado)

**Implementação**: `database.py`

**Estrutura de Dados**:
```python
# Estrutura JSON espelhada ao código
{
  "user_id_123": {
    "total_seconds": 3600,  # Atributos
    "sessions": 5           # do "record"
  }
}
```

**Métodos "Active Record"**:
```python
# "Find" - Carregar todos os records
def load_data() -> Dict[str, Dict[str, int]]

# "Save" - Persistir todos os records
def save_data(data: Dict[str, Dict[str, int]]) -> None

# "Update" - Atualizar um record específico
def update_video_time(user_id: str, duration: int) -> None
```

**Características**:
- Cada entrada de usuário é um "record" com comportamento
- Métodos de CRUD implementados diretamente no módulo
- **Simplificação**: Sem classes explicitamente, usa dicts nativos

**Benefícios**:
- ✅ Simplicidade para MVP
- ✅ Legibilidade direta do JSON
- ✅ Fácil migração para ORM futuro (SQLAlchemy)
- ✅ Baixo overhead de abstração

**Limitações**:
- ❌ Sem validação de schema em tempo de execução
- ❌ Sem relamentos ou constraints
- ❌ Refatoração necessária para migração a banco de dados

### 4.2 Lazy Loading

**Implementação**: `commands.py` + `utils.py`

**Código**:
```python
# Fetch users sob demanda (não pré-carrega todos)
member_tasks = [
    fetch_user(guild, user_id)
    for user_id, _ in sorted_users[:MAX_RANKING_SIZE]
]
members = await asyncio.gather(*member_tasks, return_exceptions=True)
```

**Características**:
- Apenas **top 10 usuários** são buscados na API Discord
- **Paralelização** com `asyncio.gather()` reduz latência
- Não carrega todos os membros do servidor (economia de rate limits)

**Benefícios**:
- ✅ Performance: ~10x mais rápido (2-5s → 200-500ms)
- ✅ Economia de rate limits da API Discord
- ✅ Escalabilidade: Funciona bem com servidores grandes

**Limitações**:
- ❌ Ainda dependente de rate limits do Discord
- ❌ Não implementa caching local

### 4.3 Facade Pattern

**Implementação**: `bot.py`

**Código**:
```python
# Facade que esconde complexidade dos módulos internos
@bot.command(name='rankingvideo')
async def ranking_video_command(ctx: commands.Context) -> None:
    from commands import ranking_video
    await ranking_video(ctx)

@bot.event
async def on_voice_state_update(member, before, after):
    from events import on_voice_state_update as voice_handler
    await voice_handler(member, before, after)
```

**Características**:
- `bot.py` atua como **fachada** para o sistema
- Esconde complexidade de `events.py`, `commands.py`, `database.py`
- Fornece interface unificada para inicialização

**Benefícios**:
- ✅ Manutenibilidade: Ponto único de configuração
- ✅ Testabilidade: Fácil mock da interface
- ✅ Evolubilidade: Fácil adicionar novos eventos/comandos

**Limitações**:
- ❌ Import dinâmico pode esconder erros em runtime
- ❌ Acoplamento indireto entre módulos

### 4.4 Manager Pattern

**Implementação**: `events.py::VideoSessionManager`

**Código**:
```python
class VideoSessionManager:
    """Gerenciador de sessões com proteção de concorrência"""
    def __init__(self):
        self._sessions: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def start_session(self, user_id: str, timestamp: datetime) -> None:
        async with self._lock:
            self._sessions[user_id] = timestamp

    async def end_session(self, user_id: str) -> Optional[datetime]:
        async with self._lock:
            return self._sessions.pop(user_id, None)
```

**Características**:
- Encapsula **estado global** (`active_video_sessions`)
- Fornece interface **controlada** (`start_session`, `end_session`)
- Implementa **locks** para prevenir race conditions

**Benefícios**:
- ✅ Thread-safety: Operações atômicas com `asyncio.Lock()`
- ✅ Testabilidade: Fácil mock e testes de concorrência
- ✅ Manutenibilidade: Responsabilidade única
- ✅ Encapsulamento: Esconde complexidade de concorrência

**Limitações**:
- ❌ Estado em memória (perdido em restart)
- ❌ Não implementa persistência periódica

### 4.5 Strategy Pattern (Implícito)

**Implementação**: Persistência em `database.py`

**Interface Atual (JSON)**:
```python
def load_data() -> Dict[str, Dict[str, int]]
def save_data(data: Dict[str, Dict[str, int]]) -> None
def update_video_time(user_id: str, duration: int) -> None
```

**Futura Implementação (SQLite)**:
```python
# Mesma interface, backend diferente
def load_data() -> List[UserModel]
def save_data(data: List[UserModel]) -> None
def update_video_time(user_id: str, duration: int) -> None
```

**Características**:
- Interface de persistência **bem definida**
- Preparado para **trocar estratégias** (JSON → SQLite → PostgreSQL)
- Backends de persistência **intercambiáveis**

**Benefícios**:
- ✅ Evolubilidade: Migração facilitada (Fases 2/3)
- ✅ Testabilidade: Fácil implementar fake backend
- ✅ Flexibilidade: Troca de estratégia sem quebrar código

---

## 5. Diagrama de Componentes

### 5.1 Visão Macro

```
                    DISCORD GATEWAY
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │         bot.py (Facade)              │
        │  ┌────────────────────────────────┐  │
        │  │  create_bot()                  │  │
        │  │  - Configura Intents           │  │
        │  │  - Registra Events/Commands    │  │
        │  │  - Error Handler Global        │  │
        │  └────────────────────────────────┘  │
        └──────────────────────────────────────┘
                    │                   │
        ┌───────────┴───────────┐       │
        ▼                       ▼       │
┌────────────────┐      ┌──────────────┤
│  events.py     │      │ commands.py  │
│ ┌────────────┐ │      │ ┌──────────┐ │
│ │VideoSession│ │      │ │ranking   │ │
│ │Manager     │ │      │ │_video()  │ │
│ │(Locks)     │ │      │ │(Lazy)    │ │
│ └────────────┘ │      │ └──────────┘ │
│                │      │              │
│ on_voice_      │      │ fetch_user() │◄─────┐
│ state_update() │      │ (parallel)   │      │
└────────────────┘      └──────────────┤      │
        │                               │      │
        ▼                               ▼      │
┌────────────────────────────────────────────────┘
│           database.py (Active Record)          │
│  ┌────────────────────────────────────────┐   │
│  │  load_data()                           │   │
│  │  save_data()                           │   │
│  │  update_video_time()                   │   │
│  └────────────────────────────────────────┘   │
└────────────────────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────────────┐
│  video_ranking.json                            │
│  {                                            │
│    "user_id": {                               │
│      "total_seconds": 3600,                   │
│      "sessions": 5                            │
│    }                                          │
│  }                                            │
└────────────────────────────────────────────────┘

Dependências Externas:
- config.py: Configurações centralizadas
- utils.py: Funções auxiliares (formatação, validação)
- tests/: Suíte de testes (pytest, 82% cobertura)
```

### 5.2 Fluxos de Dados Principais

#### Fluxo 1: Rastreamento de Câmera
```
Discord Event → events.py → VideoSessionManager
→ (session end) → database.py → video_ranking.json
```

#### Fluxo 2: Consulta de Ranking
```
User Command → commands.py → database.py (load)
→ utils.py (fetch_user, parallel) → commands.py (format)
→ Discord Embed Response
```

#### Fluxo 3: Inicialização
```
bot.py → config.py (Intents, logger)
→ events.py (register) → commands.py (register)
→ Discord Connection
```

---

## 6. Relação com PRD.md (Seções 1-4)

### 6.1 Mapeamento de Requisitos

| PRD Seção | Requisito | Implementação | Status |
|-----------|-----------|---------------|--------|
| **Seção 1 - Visão Geral** | Propósito do bot | bot.py + events.py | ✅ |
| **Seção 2 - Requisitos Funcionais** | RF01: Rastreamento câmera | events.py | ✅ |
| **Seção 2 - Requisitos Funcionais** | RF04: Comando ranking | commands.py | ✅ |
| **Seção 2 - Requisitos Funcionais** | RF06: Persistência JSON | database.py | ✅ |
| **Seção 2 - Requisitos Funcionais** | RF07: Sessões ativas | VideoSessionManager | ✅ |
| **Seção 3 - Requisitos Não-Funcionais** | RNF01: Performance < 2s | asyncio.gather() | ✅ |
| **Seção 3 - Requisitos Não-Funcionais** | RNF02: JSON < 10KB | database.py | ✅ |
| **Seção 3 - Requisitos Não-Funcionais** | RNF10: Type hints | Todos os módulos | ✅ |
| **Seção 4 - Arquitetura Técnica** | Stack Python 3.10+ | requirements.txt | ✅ |
| **Seção 4 - Arquitetura Técnica** | discord.py 2.3+ | bot.py | ✅ |
| **Seção 4 - Arquitetura Técnica** | Estrutura de arquivos | 6 módulos Python | ✅ |
| **Seção 4 - Arquitetura Técnica** | Intents necessários | config.py | ✅ |

### 6.2 Gaps vs. PRD

**Funcionalidades Não Implementadas (Fase 2)**:
- ❌ RF02: Rastreamento de tempo em voz
- ❌ RF03: Rastreamento de mensagens
- ❌ RF05: Comando `!meustats`

**Requisitos Não-Funcionais Parciais**:
- ⚠️ RNF04: Disponibilidade 99% (sem auto-restart)
- ⚠️ RNF14: Preparado para SQLite > 100 usuários (arquitetura permite, mas não implementado)

---

## 7. Considerações de Evolução

### 7.1 Fase 2 - Curto Prazo

**Objetivos**:
- Persistência de sessões ativas (resolver UC04)
- Comando `!meustats` (estatísticas individuais)
- File locking em `database.py`
- Cooldown em comandos

**Mudanças Arquiteturais**:
- `VideoSessionManager`: Adicionar persistência periódica
- `database.py`: Implementar file locking
- `commands.py`: Adicionar novo comando
- `bot.py`: Implementar cooldown via `commands.CooldownMapping`

### 7.2 Fase 3 - Longo Prazo

**Objetivos**:
- Migração para SQLite (100-1.000 usuários)
- Suporte a multi-guild
- Sistema de backup automático

**Mudanças Arquiteturais**:
- `database.py`: Refatorar para SQLite
- Estrutura de dados: Adicionar `guild_id` como chave primária
- Migration script: JSON → SQLite

### 7.3 Fase 4 - Escala

**Objetivos**:
- Migração para PostgreSQL (1.000+ usuários)
- Pool de conexões
- Replicação e backup avançado

**Mudanças Arquiteturais**:
- `database.py`: Refatorar para SQLAlchemy ou asyncpg
- Configuração: Connection pooling
- Infraestrutura: PostgreSQL cluster

---

## 8. Conclusão

A arquitetura do **Bate-Ponto** foi projetada com **simplicidade e performance** em mente, utilizando Python 3.10+ e discord.py 2.x. A organização em **4 camadas** (Apresentação, Aplicação, Domínio, Persistência) e a aplicação de **padrões arquiteturais** (Active Record, Lazy Loading, Facade, Manager, Strategy) garantem um código **manutenível, testável e evolutivo**.

**Pontos Fortes**:
- ✅ Separação clara de responsabilidades
- ✅ Padrões arquiteturais bem aplicados
- ✅ Performance otimizada com async/await
- ✅ Testes abrangentes (82% cobertura)
- ✅ Código 100% tipado com type hints

**Limitações Conhecidas**:
- ⚠️ Escala limitada a ~100 usuários (JSON)
- ⚠️ Single-guild (multi-guild não suportado)
- ⚠️ Sessões ativas não persistem em restart
- ⚠️ Sem file locking em `database.py`

**Próximos Passos**:
- Fase 2: Persistência de sessões, file locking, cooldown
- Fase 3: Migração para SQLite, multi-guild
- Fase 4: Migração para PostgreSQL, larga escala

---

**Documentação Relacionada**:
- **PRD.md**: Requisitos completos do produto
- **ARQUITETURA.md**: Documentação técnica detalhada
- **FASE1_RELATARIO.md**: Relatório da Fase 1
- **README.md**: Documentação de usuário
