"""
Funções utilitárias para o bot Discord de ranking de atividade.

Este módulo fornece funções auxiliares para formatação de tempo,
validação de dados e configuração de logs estruturados.
"""

import logging
import re
import discord
from typing import Optional


def format_seconds_to_time(seconds: int) -> str:
    """
    Converte segundos em formato legível.

    Formatos possíveis:
    - "Xh Ymin" para durações >= 1 hora
    - "Xmin" para durações >= 1 minuto
    - "Xs" para durações < 1 minuto

    Args:
        seconds: Tempo total em segundos (inteiro não-negativo)

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
        raise ValueError("seconds deve ser um inteiro não-negativo")

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
    Valida se um ID de usuário Discord é válido.

    Conforme RNF09, IDs válidos do Discord são snowflakes de 18-19 dígitos.
    Esta função implementa a validação básica de formato.

    Args:
        user_id: String contendo o ID do usuário

    Returns:
        True se o ID tem formato válido, False caso contrário

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

    # Discord snowflake IDs são 18-19 dígitos numéricos
    pattern = r"^\d{18,19}$"
    return bool(re.match(pattern, user_id))


def validate_seconds(seconds: int) -> bool:
    """
    Valida se um valor em segundos é válido.

    Args:
        seconds: Valor em segundos a validar

    Returns:
        True se seconds é um inteiro não-negativo, False caso contrário
    """
    return isinstance(seconds, int) and seconds >= 0


def setup_logger(
    name: str = "bate-ponto",
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configura um logger estruturado conforme RNF11.

    Formata logs com timestamp, nível, nome do módulo e mensagem.
    Suporta saída em console e/ou arquivo.

    Args:
        name: Nome do logger (default: "bate-ponto")
        level: Nível de log (default: logging.INFO)
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
        default: Valor padrão em caso de erro

    Returns:
        Inteiro convertido ou valor padrão
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_int_conversion(value: str) -> int:
    """
    Converte string para int com validação rigorosa.

    Args:
        value: String a converter

    Returns:
        int: Valor convertido

    Raises:
        ValueError: Se a string não for um número válido
        TypeError: Se o valor não for string
    """
    if not isinstance(value, str):
        raise TypeError("O valor deve ser uma string")

    try:
        return int(value)
    except ValueError as e:
        raise ValueError(f"Não é possível converter '{value}' para inteiro") from e


def validate_and_convert_user_id(user_id: str) -> int:
    """
    Valida e converte user_id de string para int.

    Args:
        user_id: ID do usuário como string

    Returns:
        int: ID do usuário convertido para inteiro

    Raises:
        ValueError: Se o user_id não for válido
        TypeError: Se o user_id não for string
    """
    if not isinstance(user_id, str):
        raise TypeError("user_id deve ser uma string")

    # Validar formato básico (18-19 dígitos)
    if not validate_user_id(user_id):
        raise ValueError(f"Formato de user_id inválido: {user_id}")

    try:
        return int(user_id)
    except ValueError as e:
        raise ValueError(f"Erro ao converter user_id para inteiro: {user_id}") from e


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Trunca uma string se exceder o tamanho máximo.

    Args:
        text: Texto a truncar
        max_length: Comprimento máximo permitido
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
    Busca informações de um usuário pelo ID.

    Conforme RNF06: Tratamento de erros para usuários inexistentes/deletados.
    Esta função trata exceções silenciosamente, retornando None quando o
    usuário não pode ser encontrado.

    Args:
        guild: Objeto Guild do Discord onde buscar o usuário
        user_id: ID do usuário a buscar (string)

    Returns:
        Optional[discord.Member]: Objeto Member ou None se não encontrado.

    Example:
        >>> member = await fetch_user(guild, "123456789012345678")
        >>> if member:
        ...     print(member.display_name)
    """
    try:
        # Validar e converter user_id antes de usar na API
        converted_id = validate_and_convert_user_id(user_id)
        return await guild.fetch_member(converted_id)
    except (ValueError, TypeError, discord.NotFound, discord.HTTPException):
        return None
