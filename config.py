"""
Configurações e constantes do bot Discord de ranking.

Este módulo centraliza todas as configurações do bot, incluindo:
- Carregamento de variáveis de ambiente via .env
- Constantes do projeto (prefixo, caminhos, cores)
- Configuração de Intents do Discord
- Configuração de logger estruturado
"""
from os import getenv
from logging import INFO, basicConfig, getLogger, Logger
from typing import Optional

import discord
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# ============================================================================
# CONSTANTES DO PROJETO
# ============================================================================

DISCORD_TOKEN: str = getenv("DISCORD_TOKEN", "")
COMMAND_PREFIX: str = getenv("COMMAND_PREFIX", "!")

# Arquivo de persistência de dados
DATA_FILE: str = "video_ranking.json"

# Configurações do Embed de ranking
EMBED_COLOR: int = 0x5865F2  # Azul Discord (#5865F2)
MAX_RANKING_SIZE: int = 10

# Formato de tempo para logs
TIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"


# ============================================================================
# CONFIGURAÇÃO DE INTENTS
# ============================================================================

def get_intents() -> discord.Intents:
    """
    Configura e retorna os Intents necessários para o bot.

    Os Intents definem quais eventos o bot pode receber do Discord.
    Para rastreamento de câmera, precisamos de:
    - guilds: Para operações básicas de servidor
    - voice_states: Para detectar mudanças de estado de voz (câmera)
    - members: Para buscar informações de usuários (fetch_user)

    Returns:
        discord.Intents: Objeto de Intents configurado para o bot.

    Example:
        >>> intents = get_intents()
        >>> bot = commands.Bot(command_prefix="!", intents=intents)
    """
    intents = discord.Intents.default()
    intents.guilds = True
    intents.voice_states = True
    intents.members = True  # Necessário para fetch_user em ranking
    return intents


# ============================================================================
# CONFIGURAÇÃO DE LOGGER
# ============================================================================

def setup_logger(name: Optional[str] = None, level: int = INFO) -> Logger:
    """
    Configura e retorna um logger estruturado para o bot.

    O logger é configurado com formato estruturado para facilitar debug
    e monitoramento do bot em produção.

    Args:
        name: Nome do logger (default: None usa o logger root).
        level: Nível de log (default: INFO).

    Returns:
        Logger: Objeto de logger configurado.

    Example:
        >>> logger = setup_logger("bot")
        >>> logger.info("Bot iniciado com sucesso")
    """
    basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt=TIME_FORMAT,
        level=level,
    )
    return getLogger(name or __name__)
