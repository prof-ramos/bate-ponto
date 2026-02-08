Vou criar um PRD (Product Requirements Document) completo para o projeto de bot Discord de ranking de atividade:

```markdown
# Product Requirements Document (PRD)
## Bot de Ranking de Atividade Discord

---

## 1. Visão Geral do Projeto

### 1.1 Contexto
Bot Discord para rastreamento e ranking de atividade de membros em servidores, com foco principal em tempo de participação com câmera ligada em canais de voz.

### 1.2 Objetivo
Gamificar e incentivar a participação ativa dos membros através de métricas visíveis de engajamento, especialmente uso de câmera em reuniões/chamadas.

### 1.3 Escopo
- **Público-alvo**: Servidores Discord com até 50 membros ativos
- **Plataforma**: Discord (desktop/mobile/web)
- **Tecnologia**: Python 3.10+, discord.py 2.x, JSON para persistência

---

## 2. Requisitos Funcionais

### 2.1 Rastreamento de Atividade

#### RF01 - Rastreamento de Tempo com Câmera
**Prioridade**: Alta
**Descrição**: O bot deve rastrear automaticamente quando usuários ligam/desligam câmera em canais de voz.

**Critérios de Aceitação**:
- Detectar evento `self_video = True` no `on_voice_state_update`
- Registrar timestamp de início quando câmera é ligada
- Calcular duração quando câmera é desligada
- Acumular tempo total por usuário
- Registrar número de sessões com câmera

**Métricas Rastreadas**:
- `total_seconds`: Tempo acumulado em segundos
- `sessions`: Número de vezes que ligou câmera
- `last_updated`: Timestamp da última atividade

#### RF02 - Rastreamento de Tempo em Voz (Opcional - Fase 2)
**Prioridade**: Média
**Descrição**: Rastrear tempo total em canais de voz (com ou sem câmera).

#### RF03 - Rastreamento de Mensagens (Opcional - Fase 2)
**Prioridade**: Baixa
**Descrição**: Contar mensagens enviadas por usuário.

### 2.2 Sistema de Ranking

#### RF04 - Comando de Leaderboard
**Prioridade**: Alta
**Comando**: `!rankingvideo`

**Funcionalidade**:
- Exibir top 10 usuários por tempo com câmera
- Formato: Embed Discord com estilização
- Informações por usuário:
  - Posição no ranking (#1, #2, etc.)
  - Nome/avatar do usuário
  - Tempo total (formato: Xh Ymin)
  - Número de sessões
- Ordenação: Decrescente por `total_seconds`

**Resposta quando vazio**: Mensagem amigável informando ausência de dados

#### RF05 - Comando de Estatísticas Individual (Opcional - Fase 2)
**Prioridade**: Baixa
**Comando**: `!meustats` ou `!stats @usuario`

**Funcionalidade**:
- Exibir estatísticas detalhadas de um usuário específico
- Informações: ranking atual, tempo total, sessões, média por sessão

### 2.3 Persistência de Dados

#### RF06 - Armazenamento JSON
**Prioridade**: Alta
**Arquivo**: `video_ranking.json`

**Estrutura**:
```json
{
  "user_id_1": {
    "total_seconds": 3600,
    "sessions": 5
  },
  "user_id_2": {
    "total_seconds": 7200,
    "sessions": 10
  }
}
```

**Operações**:
- Leitura: Ao iniciar comandos de ranking
- Escrita: Sempre que uma sessão de câmera termina
- Inicialização: Criar arquivo vazio {} se não existir

#### RF07 - Gestão de Sessões Ativas
**Prioridade**: Alta
**Descrição**: Manter dicionário em memória com sessões ativas.

**Estrutura**:
```python
active_video_sessions = {
  "user_id": datetime_object
}
```

**Comportamento**:
- Adicionar entrada quando câmera liga
- Remover e calcular duração quando câmera desliga
- Limpar se usuário sai do servidor/canal abruptamente

---

## 3. Requisitos Não-Funcionais

### 3.1 Performance
- **RNF01**: Resposta de comandos em < 2 segundos para 50 usuários
- **RNF02**: Arquivo JSON deve ter < 10KB para 50 usuários
- **RNF03**: Bot deve usar < 100MB de RAM em operação normal

### 3.2 Confiabilidade
- **RNF04**: Disponibilidade de 99% (mínimo 23h45min/dia)
- **RNF05**: Não perder dados de sessões concluídas mesmo em restart
- **RNF06**: Tratamento de erros para usuários inexistentes/deletados

### 3.3 Segurança
- **RNF07**: Token do bot em variável de ambiente (.env)
- **RNF08**: Permissões mínimas necessárias (intents: guilds, voice_states)
- **RNF09**: Validação de IDs de usuário antes de queries

### 3.4 Manutenibilidade
- **RNF10**: Código em Python com type hints
- **RNF11**: Logs estruturados para debug (console)
- **RNF12**: Arquivo JSON legível (indent=2)
- **RNF13**: Funções modulares e reutilizáveis

### 3.5 Escalabilidade
- **RNF14**: Preparado para migração futura para SQLite se > 100 usuários
- **RNF15**: Estrutura de dados extensível para novas métricas

---

## 4. Arquitetura Técnica

### 4.1 Stack Tecnológico
- **Linguagem**: Python 3.10+
- **Biblioteca Discord**: discord.py 2.3+
- **Persistência**: JSON (biblioteca nativa `json`)
- **Gestão de tempo**: `datetime` (biblioteca nativa)
- **Deploy**: VPS Ubuntu 22.04+ ou container Docker

### 4.2 Intents Necessários
```python
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.members = True  # Para fetch_user
```

### 4.3 Estrutura de Arquivos
```
discord-ranking-bot/
├── bot.py              # Arquivo principal
├── config.py           # Configurações e constantes
├── database.py         # Funções de persistência
├── commands.py         # Comandos do bot
├── events.py           # Event handlers
├── utils.py            # Funções auxiliares
├── .env                # Variáveis de ambiente
├── requirements.txt    # Dependências
├── video_ranking.json  # Dados (gerado automaticamente)
└── README.md          # Documentação
```

### 4.4 Componentes Principais

#### 4.4.1 Event Handler - Voice State
```python
@bot.event
async def on_voice_state_update(member, before, after)
```
- Detecta mudanças em `self_video`
- Registra timestamps de início/fim
- Atualiza JSON ao fim de sessão

#### 4.4.2 Data Manager
```python
def load_data() -> dict
def save_data( dict) -> None
def update_video_time(user_id: str, duration: int) -> None
```

#### 4.4.3 Command Handler - Ranking
```python
@bot.command(name='rankingvideo')
async def ranking_video(ctx)
```
- Carrega dados do JSON
- Ordena por `total_seconds`
- Formata e envia embed

---

## 5. Casos de Uso

### UC01 - Usuário Liga Câmera
**Ator**: Membro do servidor
**Fluxo**:
1. Usuário entra em canal de voz
2. Usuário ativa câmera
3. Bot detecta `self_video = True`
4. Bot salva timestamp em `active_video_sessions`
5. Bot loga ação no console

**Resultado**: Início de rastreamento registrado

### UC02 - Usuário Desliga Câmera
**Ator**: Membro do servidor
**Fluxo**:
1. Usuário desativa câmera
2. Bot detecta `self_video = False`
3. Bot calcula duração: `datetime.now() - start_time`
4. Bot atualiza JSON com duração acumulada
5. Bot incrementa contador de sessões
6. Bot remove entrada de `active_video_sessions`
7. Bot loga duração no console

**Resultado**: Tempo registrado e persistido

### UC03 - Administrador Consulta Ranking
**Ator**: Administrador ou membro
**Fluxo**:
1. Usuário digita `!rankingvideo`
2. Bot carrega `video_ranking.json`
3. Bot ordena usuários por `total_seconds`
4. Bot busca informações dos top 10 usuários
5. Bot cria embed formatado
6. Bot envia embed no canal

**Fluxo Alternativo**: Se JSON vazio, envia mensagem de ausência de dados

**Resultado**: Ranking exibido visualmente

### UC04 - Bot Reinicia Durante Sessão Ativa
**Ator**: Sistema
**Fluxo**:
1. Bot está rastreando sessões ativas em memória
2. Bot é desligado/reiniciado
3. Sessões ativas em `active_video_sessions` são perdidas
4. Bot reinicia e aguarda novos eventos

**Problema Conhecido**: Sessões ativas não persistem
**Solução Futura (Fase 2)**: Salvar sessões ativas periodicamente

---

## 6. Interface do Usuário

### 6.1 Embed de Ranking
```
┌─────────────────────────────────────┐
│ 🎥 Ranking - Tempo com Câmera Ligada│
├─────────────────────────────────────┤
│ #1 João Silva                       │
│ ⏱️ 12h 35min                        │
│ 📹 23 sessões                        │
├─────────────────────────────────────┤
│ #2 Maria Santos                     │
│ ⏱️ 8h 42min                         │
│ 📹 15 sessões                        │
├─────────────────────────────────────┤
│ ... (até 10 posições)               │
└─────────────────────────────────────┘
```

**Cores**: Azul Discord (#5865F2)
**Ícones**: 🎥 📹 ⏱️
**Formato**: `inline=False` para melhor legibilidade

### 6.2 Logs do Console
```
📹 João Silva ligou a câmera
📹 Maria Santos ligou a câmera
📹 João Silva desligou - 1847s gravados
✅ Bot conectado como RankingBot#1234
```

---

## 7. Dependências

### 7.1 requirements.txt
```
discord.py>=2.3.0
python-dotenv>=1.0.0
```

### 7.2 Variáveis de Ambiente (.env)
```
DISCORD_TOKEN=seu_token_aqui
COMMAND_PREFIX=!
```

---

## 8. Roadmap de Desenvolvimento

### Fase 1 - MVP (Semana 1)
- ✅ Setup básico do bot
- ✅ Event handler para `self_video`
- ✅ Persistência JSON
- ✅ Comando `!rankingvideo`
- ✅ Logs básicos

### Fase 2 - Melhorias (Semana 2-3)
- ⬜ Persistência de sessões ativas
- ⬜ Comando `!meustats`
- ⬜ Rastreamento de tempo em voz
- ⬜ Sistema de backup automático
- ⬜ Comando admin para reset de dados

### Fase 3 - Expansão (Futuro)
- ⬜ Rastreamento de mensagens
- ⬜ Sistema de XP e níveis
- ⬜ Atribuição automática de cargos
- ⬜ Dashboard web
- ⬜ Migração para PostgreSQL

---

## 9. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Perda de dados por crash | Média | Alto | Salvar imediatamente após cada sessão |
| Bot offline durante eventos | Baixa | Médio | Monitoramento com uptime service |
| Spam de comandos | Baixa | Baixo | Cooldown de 5s por usuário |
| JSON corrompido | Baixa | Alto | Backup diário + validação na leitura |
| Usuário deleta conta | Média | Baixo | Try/except em fetch_user |

---

## 10. Métricas de Sucesso

### 10.1 KPIs Técnicos
- Uptime: > 99%
- Tempo de resposta: < 2s
- Taxa de erro: < 0.1%

### 10.2 KPIs de Produto
- Usuários rastreados: 50 (meta)
- Comandos executados/dia: 10+
- Sessões de câmera/dia: 20+

### 10.3 KPIs de Engajamento
- Aumento de 30% no uso de câmera após 1 mês
- 80% dos membros ativos consultam ranking semanalmente

---

## 11. Testes

### 11.1 Casos de Teste

**TC01 - Rastreamento Básico**
- Usuário liga câmera → timestamp registrado
- Usuário desliga câmera → duração calculada corretamente
- Verificar JSON atualizado com valores corretos

**TC02 - Ranking Vazio**
- Deletar JSON ou usar JSON vazio
- Executar `!rankingvideo`
- Verificar mensagem de ausência de dados

**TC03 - Ranking com Dados**
- Popular JSON com 3 usuários
- Executar `!rankingvideo`
- Verificar ordenação correta

**TC04 - Múltiplas Sessões**
- Usuário liga/desliga câmera 3x
- Verificar `sessions = 3`
- Verificar soma correta de `total_seconds`

**TC05 - Usuário Inexistente**
- Adicionar user_id inválido no JSON
- Executar `!rankingvideo`
- Verificar skip silencioso sem erro

### 11.2 Testes de Carga
- 10 usuários simultâneos com câmera
- 50 consultas de ranking em 1 minuto
- Verificar ausência de race conditions

---

## 12. Documentação

### 12.1 README.md (Obrigatório)
- Descrição do projeto
- Requisitos e instalação
- Configuração (.env)
- Comandos disponíveis
- Como executar
- Troubleshooting

### 12.2 Comentários no Código
- Docstrings em todas as funções
- Type hints em parâmetros e retornos
- Comentários explicando lógica complexa

---

## 13. Deploy

### 13.1 Ambiente de Desenvolvimento
- Python 3.10+ local
- Servidor Discord de testes
- Bot com permissões de dev

### 13.2 Ambiente de Produção
**Opção 1: VPS Ubuntu**
- Instalar Python 3.10+
- Clonar repositório
- Configurar .env
- Executar com systemd ou screen

**Opção 2: Docker**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

**Opção 3: Railway/Render**
- Deploy automático via GitHub
- Variáveis de ambiente na plataforma

---

## 14. Permissões Discord Necessárias

### 14.1 Bot Permissions
- View Channels
- Read Message History
- Send Messages
- Embed Links

### 14.2 Privileged Gateway Intents
- Server Members Intent (para fetch_user)
- Presence Intent (opcional - para status)

### 14.3 OAuth2 URL
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=19456&scope=bot
```

---

## 15. Glossário

- **Self Video**: Estado do Discord que indica se câmera está ligada
- **Voice State Update**: Evento disparado quando há mudança em canal de voz
- **Embed**: Mensagem formatada rica do Discord
- **Intents**: Permissões de eventos que o bot pode receber
- **Guild**: Servidor Discord (terminologia da API)

---

## 16. Aprovações

| Stakeholder | Papel | Status | Data |
|-------------|-------|--------|------|
| Gabriel Ramos | Product Owner | ✅ Aprovado | 08/02/2026 |
| - | Tech Lead | Pendente | - |
| - | QA | Pendente | - |

---

## 17. Histórico de Versões

| Versão | Data | Autor | Mudanças |
|--------|------|-------|----------|
| 1.0 | 08/02/2026 | Perplexity AI | Versão inicial do PRD |

---

## 18. Anexos

### Anexo A - Exemplo de JSON
```json
{
  "123456789012345678": {
    "total_seconds": 45320,
    "sessions": 12
  },
  "987654321098765432": {
    "total_seconds": 31450,
    "sessions": 8
  }
}
```

### Anexo B - Código Mínimo Viável
(Referência ao código fornecido anteriormente na conversa)
```

Este PRD está pronto para ser usado como documento base do projeto. Ele cobre todos os aspectos necessários desde requisitos técnicos até métricas de sucesso, passando por arquitetura, casos de uso e roadmap de desenvolvimento.[1][2]

Fontes
[1] How to create a Discord bot with Python: Part 11 - Connect a sqlite3 database https://www.youtube.com/watch?v=H09U2E2v8eg
[2] JSON file VS SQLite android https://stackoverflow.com/questions/8652005/json-file-vs-sqlite-android
