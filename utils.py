"""
Funcoes utilitarias para o bot Discord de ranking de atividade.

Este modulo fornece funcoes auxiliares para formatacao de tempo,
validacao de dados e configuracao de logs estruturados.
"""

import logging
import re
import discord
from typing import Optional


def format_seconds_to_time(seconds: int) -> str:
    """
    Converte segundos em formato legivel.

    Formatos possiveis:
    - "Xh Ymin" para duracoes >= 1 hora
    - "Xmin" para duracoes >= 1 minuto
    - "Xs" para duracoes < 1 minuto

    Args:
        seconds: Tempo total em segundos (inteiro nao-negativo)

    Returns:
        String formatada representando o tempo

    Examples:
        >>> format_seconds_to_time(3665)
        '1h 1min'
        >>> format_seconds_to_time(120)
        '2min'
        >>> format_seconds_to_time(45)
        '45s'
    """
    if not isinstance(seconds, int) or seconds < 0:
        raise ValueError("seconds deve ser um inteiro nao-negativo")

    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    if minutes < 60:
        return f"{minutes}min"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0:
        return f"{hours}h"

    return f"{hours}h {remaining_minutes}min"


def validate_user_id(user_id: str) -> bool:
    """
    Valida se um ID de usuario Discord e valido.

    Conforme RNF09, IDs validos do Discord sao snowflakes de 18-19 digitos.
    Esta funcao implementa a validacao basica de formato.

    Args:
        user_id: String contendo o ID do usuario

    Returns:
        True se o ID tem formato valido, False caso contrario

    Examples:
        >>> validate_user_id("123456789012345678")
        True
        >>> validate_user_id("invalid")
        False
        >>> validate_user_id("12345")
        False
    """
    if not isinstance(user_id, str):
        return False

    # Discord snowflake IDs sao 18-19 digitos numericos
    pattern = r"^\d{18,19}$"
    return bool(re.match(pattern, user_id))


def validate_seconds(seconds: int) -> bool:
    """
    Valida se um valor em segundos e valido.

    Args:
        seconds: Valor em segundos a validar

    Returns:
        True se seconds e um inteiro nao-negativo, False caso contrario
    """
    return isinstance(seconds, int) and seconds >= 0


def setup_logger(
    name: str = "bate-ponto",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configura um logger estruturado conforme RNF11.

    Formata logs com timestamp, nivel, nome do modulo e mensagem.
    Suporta saida em console e/ou arquivo.

    Args:
        name: Nome do logger (default: "bate-ponto")
        level: Nivel de log (default: logging.INFO)
        log_file: Caminho opcional para arquivo de log

    Returns:
        Logger configurado e pronto para uso

    Examples:
        >>> logger = setup_logger()
        >>> logger.info("Bot iniciado")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evitar handlers duplicados
    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler opcional para arquivo
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def safe_int(value: str, default: int = 0) -> int:
    """
    Converte string para int de forma segura.

    Args:
        value: String a converter
        default: Valor padrao em caso de erro

    Returns:
        Inteiro convertido ou valor padrao
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Trunca uma string se exceder o tamanho maximo.

    Args:
        text: Texto a truncar
        max_length: Comprimento maximo permitido
        suffix: Sufixo a adicionar quando truncado

    Returns:
        String truncada ou original se dentro do limite
    """
    if not isinstance(text, str):
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


async def fetch_user(guild: discord.Guild, user_id: str) -> Optional[discord.Member]:
    """
    Busca informacoes de um usuario pelo ID.

    Conforme RNF06: Tratamento de erros para usuarios inexistentes/deletados.
    Esta funcao trata excecoes silenciosamente, retornando None quando o
    usuario nao pode ser encontrado.

    Args:
        guild: Objeto Guild do Discord onde buscar o usuario
        user_id: ID do usuario a buscar (string)

    Returns:
        Optional[discord.Member]: Objeto Member ou None se nao encontrado.

    Example:
        >>> member = await fetch_user(guild, "123456789012345678")
        >>> if member:
        ...     print(member.display_name)
    """
    try:
        return await guild.fetch_member(user_id)
    except (discord.NotFound, discord.HTTPException):
        return None
