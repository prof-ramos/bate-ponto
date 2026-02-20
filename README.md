# Bate-Ponto Discord Bot

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Discord](https://img.shields.io/badge/Discord.py-2.3%2B-purple)
![Tests](https://img.shields.io/badge/Tests-63%20passing-green)
![License](https://img.shields.io/badge/License-MIT-green)

## Sobre o Projeto

Bate-Ponto é um bot Discord que gamifica a participação dos membros através de um ranking de atividade baseado em tempo de câmera ligada em canais de voz. O objetivo é incentivar o engajamento visual em reuniões e chamadas, criando uma competição saudável entre membros.

### Funcionalidades Principais

- **Rastreamento automático de câmera**: Detecta quando usuários ligam/desligam câmera em tempo real
- **Sistema de ranking**: Leaderboard dos top 10 usuários por tempo com câmera
- **Persistência de dados**: Armazenamento em JSON com bloqueio de arquivo para segurança
- **Interface visual**: Embeds estilizados no Discord para melhor experiência
- **Logs estruturados**: Console logging para monitoramento e debug
- **Operações atômicas**: File locking para prevenir corrupção de dados em acesso concorrente

## Comandos Disponíveis

| Comando | Descrição | Uso |
|---------|-----------|-----|
| `!rankingvideo` | Exibe o top 10 usuários por tempo de câmera | `!rankingvideo` |

## Pré-requisitos

- **Python 3.8+**: Certifique-se de ter o Python instalado
- **Conta Discord**: Necessária para criar o bot
- **Token do Bot**: Obtido no [Discord Developer Portal](https://discord.com/developers/applications)

## Instalação

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/bate-ponto.git
cd bate-ponto
```

### 2. Crie um Ambiente Virtual (Opcional, mas Recomendado)

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# Ou
.venv\Scripts\activate     # Windows
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

Para desenvolvimento, instale também as dependências de teste:

```bash
pip install -r requirements-dev.txt
```

Ou utilizando UV (recomendado):

```bash
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt
```

## Configuração

### 1. Configure as Variáveis de Ambiente

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas credenciais:

```env
DISCORD_TOKEN=seu_token_aqui
COMMAND_PREFIX=!
```

### 2. Obtenha o Token do Bot

1. Acesse o [Discord Developer Portal](https://discord.com/developers/applications)
2. Crie uma nova aplicação
3. Vá em "Bot" e clique em "Add Bot"
4. Copie o token em "Reset Token"
5. Cole no arquivo `.env`

### 3. Configure as Permissões do Bot

O bot precisa das seguintes permissões:

- **View Channels** - Para acessar canais do servidor
- **Read Message History** - Para ler mensagens
- **Send Messages** - Para responder comandos
- **Embed Links** - Para exibir o ranking

### 4. Configure os Privileged Gateway Intents

No Discord Developer Portal, ative:

- **Server Members Intent** - Para buscar informações de usuários
- **Presence Intent** (opcional) - Para detectar status

URL de convite com permissões corretas:

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=19456&scope=bot%20applications.commands
```

## Como Executar

### Modo Desenvolvimento

```bash
python bot.py
```

Ou com UV:

```bash
uv run bot.py
```

### Modo Produção (Recomendado)

#### Usando systemd (Linux)

Crie o arquivo `/etc/systemd/system/bate-ponto.service`:

```ini
[Unit]
Description=Bate-Ponto Discord Bot
After=network.target

[Service]
Type=simple
User=seu-usuario
WorkingDirectory=/caminho/para/bate-ponto
Environment="PATH=/caminho/para/.venv/bin"
ExecStart=/caminho/para/.venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Execute:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bate-ponto
sudo systemctl start bate-ponto
```

#### Usando Docker

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

Build e run:

```bash
docker build -t bate-ponto .
docker run -d --name bate-ponto --env-file .env bate-ponto
```

## Estrutura do Projeto

```
bate-ponto/
├── bot.py                 # Ponto de entrada do bot
├── config.py              # Configurações e constantes
├── database.py            # Camada de persistência de dados
├── database_lock.py       # File locking para operações atômicas
├── events.py              # Event handlers (voice state)
├── commands.py            # Comandos do bot (ranking)
├── utils.py               # Funções utilitárias
├── requirements.txt       # Dependências de produção
├── requirements-dev.txt   # Dependências de desenvolvimento
├── pytest.ini            # Configuração do pytest
├── .env                  # Variáveis de ambiente (não commitar)
├── .env.example          # Exemplo de configuração
├── .gitignore            # Arquivos ignorados pelo git
├── video_ranking.json    # Dados do ranking (auto-criado)
├── README.md             # Documentação principal
├── ARCHITECTURE.md       # Documentação de arquitetura
├── implementation_plan.md # Plano de implementação
└── tests/                # Suite de testes
    ├── __init__.py
    ├── conftest.py       # Fixtures compartilhadas
    ├── test_database.py  # Testes de persistência
    ├── test_events.py    # Testes de event handlers
    └── test_utils.py     # Testes de funções utilitárias
```

## Documentação

Para detalhes técnicos e arquiteturais, consulte:

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Documentação completa da arquitetura do sistema
- **[implementation_plan.md](implementation_plan.md)** - Plano de implementação e correções

## Troubleshooting

### Bot não conecta

**Erro**: `LoginFailure: Improper token has been passed`

**Solução**: Verifique se o token no `.env` está correto e sem espaços extras.

### Comandos não funcionam

**Erro**: Bot não responde aos comandos

**Solução**:
1. Verifique se o prefixo está correto (default: `!`)
2. Confirme que o bot tem permissões de "Send Messages"
3. Verifique se o bot está online no servidor

### Erro de privilégios

**Erro**: `PrivilegedIntentsRequired`

**Solução**: Ative os "Privileged Gateway Intents" no Discord Developer Portal.

### Dados não são salvos

**Erro**: `video_ranking.json` não é atualizado

**Solução**: Verifique as permissões de escrita no diretório do bot.

### Bot crasha com câmera ligada

**Problema**: Sessões ativas são perdidas em restart

**Solução**: É um comportamento conhecido. Sessões ativas não persistem por enquanto. A Fase 2 do projeto irá resolver isso.

### Erro de file locking

**Erro**: `FileLockError: Timeout ao tentar bloquear arquivo`

**Solução**: Pode ocorrer em casos de alta concorrência. O sistema usa exponential backoff e deve retry automaticamente. Se persistir, verifique se há múltiplas instâncias do bot rodando.

### Permissão negada ao ler/escrever arquivo

**Erro**: `PermissionError: [Errno 13] Permission denied`

**Solução**: Verifique as permissões do diretório:

```bash
chmod +w /caminho/para/bate-ponto
```

## Desenvolvimento e Testes

### Executar Testes

```bash
# Instalar dependências de desenvolvimento
pip install -r requirements-dev.txt

# Executar todos os testes
pytest tests/ -v

# Executar com coverage
pytest tests/ --cov=. --cov-report=html

# Executar teste específico
pytest tests/test_database.py -v

# Executar testes de um arquivo específico
pytest tests/test_utils.py::TestFormatSecondsToTime -v
```

### Cobertura de Testes

O projeto mantém alta cobertura de testes:

- **63 testes** implementados e passando
- `database.py`: Cobertura abrangente incluindo testes de concorrência
- `utils.py`: Cobertura completa de funções utilitárias
- Testes de operações atômicas e file locking

### Estrutura de Testes

```
tests/
├── __init__.py
├── conftest.py              # Fixtures compartilhadas
├── test_database.py         # Testes de persistência (concorrência incluída)
├── test_events.py           # Testes de voice state handler
├── test_commands.py         # Testes de comandos
└── test_utils.py            # Testes de funções utilitárias
```

## Roadmap

### Fase 1 - MVP (Concluído)

- [x] Setup básico do bot
- [x] Event handler para `self_video`
- [x] Persistência JSON
- [x] Comando `!rankingvideo`
- [x] Logs estruturados
- [x] File locking para operações atômicas
- [x] Suite completa de testes (63 testes)
- [x] Documentação de arquitetura

### Fase 2 - Melhorias (Planejado)

- [ ] Persistência de sessões ativas
- [ ] Comando `!meustats` (estatísticas individuais)
- [ ] Rastreamento de tempo em voz
- [ ] Sistema de backup automático
- [ ] Comando admin para reset de dados
- [ ] Cooldown em comandos

### Fase 3 - Expansão (Futuro)

- [ ] Rastreamento de mensagens
- [ ] Sistema de XP e níveis
- [ ] Atribuição automática de cargos
- [ ] Dashboard web
- [ ] Migração para PostgreSQL
- [ ] API REST

## Tecnologias Utilizadas

| Componente | Tecnologia |
|------------|------------|
| Linguagem | Python 3.8+ |
| Discord API | discord.py >= 2.3.0 |
| Configuração | python-dotenv >= 1.0.0 |
| Armazenamento | JSON (video_ranking.json) |
| File Locking | portalocker >= 3.2.0 |
| Testes | pytest >= 9.0.2 |

## Suporte

Se encontrar problemas ou tiver sugestões:

1. Abra uma issue no GitHub
2. Consulte o [ARCHITECTURE.md](ARCHITECTURE.md) para detalhes técnicos
3. Verifique os logs do bot no console

## Licença

MIT License - Veja o arquivo LICENSE para detalhes.

## Créditos

Desenvolvido para gamificar a participação em servidores Discord.

---

**Nota**: Este bot deve ser usado de acordo com os Termos de Serviço do Discord. O rastreamento de câmera é feito apenas para fins de gamificação e todos os dados são armazenados localmente.
