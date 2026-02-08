# Bate-Ponto Discord Bot

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Discord](https://img.shields.io/badge/Discord.py-2.3%2B-purple)
![License](https://img.shields.io/badge/License-MIT-green)

## Sobre o Projeto

Bate-Ponto e um bot Discord que gamifica a participacao dos membros atraves de um ranking de atividade baseado em tempo de camera ligada em canais de voz. O objetivo e incentivar o engajamento visual em reunioes e chamadas, criando uma competencia saudavel entre membros.

### Funcionalidades Principais

- **Rastreamento automatico de camera**: Detecta quando usuarios ligam/desligam camera em tempo real
- **Sistema de ranking**: Leaderboard dos top 10 usuarios por tempo com camera
- **Persistencia de dados**: Armazenamento em JSON para garantir que dados nao sejam perdidos
- **Interface visual**: Embeds estilizados no Discord para melhor experiencia
- **Logs estruturados**: Console logging para monitoramento e debug

## Comandos Disponiveis

| Comando | Descricao | Uso |
|---------|-----------|-----|
| `!rankingvideo` | Exibe o top 10 usuarios por tempo de camera | `!rankingvideo` |

## Pre-requisitos

- **Python 3.10+**: Certifique-se de ter o Python instalado
- **Conta Discord**: Necessaria para criar o bot
- **Token do Bot**: Obtido no [Discord Developer Portal](https://discord.com/developers/applications)

## Instalacao

### 1. Clone o Repositorio

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

### 3. Instale as Dependencias

```bash
pip install -r requirements.txt
```

Ou utilizando UV (recomendado):

```bash
uv pip install -r requirements.txt
```

## Configuracao

### 1. Configure as Variaveis de Ambiente

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
2. Crie uma nova aplicacao
3. Va em "Bot" e clique em "Add Bot"
4. Copie o token em "Reset Token"
5. Cole no arquivo `.env`

### 3. Configure as Permissoes do Bot

O bot precisa das seguintes permissoes:

- **View Channels** - Para acessar canais do servidor
- **Read Message History** - Para ler mensagens
- **Send Messages** - Para responder comandos
- **Embed Links** - Para exibir o ranking

### 4. Configure os Privileged Gateway Intents

No Discord Developer Portal, ative:

- **Server Members Intent** - Para buscar informacoes de usuarios
- **Presence Intent** (opcional) - Para detectar status

URL de convite com permissoes corretas:

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

### Modo Producao (Recomendado)

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
├── bot.py              # Arquivo principal do bot
├── .env                # Variaveis de ambiente (nao commitar)
├── .env.example        # Exemplo de configuracao
├── .gitignore          # Arquivos ignorados pelo git
├── requirements.txt    # Dependencias Python
├── video_ranking.json  # Dados do ranking (gerado automaticamente)
├── README.md           # Documentacao
└── PRD.md             # Product Requirements Document
```

## Troubleshooting

### Bot nao conecta

**Erro**: `LoginFailure: Improper token has been passed`

**Solucao**: Verifique se o token no `.env` esta correto e sem espacos extras.

### Comandos nao funcionam

**Erro**: Bot nao responde aos comandos

**Solucao**:
1. Verifique se o prefixo esta correto (default: `!`)
2. Confirme que o bot tem permissoes de "Send Messages"
3. Verifique se o bot esta online no servidor

### Erro de privilegios

**Erro**: `PrivilegedIntentsRequired`

**Solucao**: Ative os "Privileged Gateway Intents" no Discord Developer Portal.

### Dados nao sao salvos

**Erro**: `video_ranking.json` nao e atualizado

**Solucao**: Verifique as permissoes de escrita no diretorio do bot.

### Bot crasha com camera ligada

**Problema**: Sessoes ativas sao perdidas em restart

**Solucao**: E um comportamento conhecido. Sessoes ativas nao persistem por enquanto. A Fase 2 do projeto ira resolver isso.

### Permissao negada ao ler/escrever arquivo

**Erro**: `PermissionError: [Errno 13] Permission denied`

**Solucao**: Verifique as permissoes do diretorio:

```bash
chmod +w /caminho/para/bate-ponto
```

## Desenvolvimento e Testes

### Executar Testes

```bash
pip install -r requirements.txt
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
pytest tests/test_database.py -v
pytest tests/integration/ -v
```

### Estrutura de Testes

```
tests/
├── conftest.py              # Fixtures compartilhadas
├── test_database.py         # Testes de persistencia
├── test_events.py           # Testes de voice state handler
├── test_commands.py         # Testes de comandos
├── test_utils.py            # Testes de funcoes utilitarias
├── integration/             # Testes de integracao
│   └── test_integration.py
└── benchmark/               # Benchmarks de performance
    └── performance_test.py
```

### Cobertura de Testes

O projeto mantem cobertura de testes acima de 80% para os módulos core:

- `database.py`: 97% de cobertura
- `utils.py`: 86% de cobertura
- Cobertura geral: 82%

## Roadmap

### Fase 1 - MVP (Concluido)

- [x] Setup basico do bot
- [x] Event handler para `self_video`
- [x] Persistencia JSON
- [x] Comando `!rankingvideo`
- [x] Logs basicos

### Fase 2 - Melhorias (Planejado)

- [ ] Persistencia de sessoes ativas
- [ ] Comando `!meustats` (estatisticas individuais)
- [ ] Rastreamento de tempo em voz
- [ ] Sistema de backup automatico
- [ ] Comando admin para reset de dados
- [ ] Cooldown em comandos

### Fase 3 - Expansao (Futuro)

- [ ] Rastreamento de mensagens
- [ ] Sistema de XP e niveis
- [ ] Atribuicao automatica de cargos
- [ ] Dashboard web
- [ ] Migracao para PostgreSQL
- [ ] API REST

## Suporte

Se encontrar problemas ou tiver sugestoes:

1. Abra uma issue no GitHub
2. Consulte o [PRD.md](PRD.md) para detalhes tecnicos
3. Verifique os logs do bot no console

## Licenca

MIT License - Veja o arquivo LICENSE para detalhes.

## Creditos

Desenvolvido para gamificar a participacao em servidores Discord.

---

**Nota**: Este bot deve ser usado de acordo com os Termos de Servico do Discord. O rastreamento de camera e feito apenas para fins de gamificacao e todos os dados sao armazenados localmente.
