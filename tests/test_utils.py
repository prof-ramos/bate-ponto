"""Tests para utils.py - funções utilitárias."""
import pytest
from utils import (
    format_seconds_to_time,
    validate_user_id,
    validate_seconds,
    safe_int,
    safe_int_conversion,
    validate_and_convert_user_id,
    truncate_string,
    setup_logger
)


class TestFormatSecondsToTime:
    """Testes para função format_seconds_to_time."""

    def test_format_seconds_to_time_seconds_only(self):
        """Teste: formata segundos menores que 1 minuto."""
        assert format_seconds_to_time(0) == "0s"
        assert format_seconds_to_time(30) == "30s"
        assert format_seconds_to_time(59) == "59s"

    def test_format_seconds_to_time_minutes_only(self):
        """Teste: formata segundos entre 1 minuto e 1 hora."""
        assert format_seconds_to_time(60) == "1min"
        assert format_seconds_to_time(120) == "2min"
        assert format_seconds_to_time(3599) == "59min"

    def test_format_seconds_to_time_hours_only(self):
        """Teste: formata segundos exatamente 1 hora ou mais."""
        assert format_seconds_to_time(3600) == "1h"
        assert format_seconds_to_time(7200) == "2h"
        assert format_seconds_to_time(86400) == "24h"

    def test_format_seconds_to_time_hours_and_minutes(self):
        """Teste: formata segundos com horas e minutos."""
        assert format_seconds_to_time(3660) == "1h 1min"
        assert format_seconds_to_time(3665) == "1h 1min"
        assert format_seconds_to_time(7320) == "2h 2min"

    def test_format_seconds_to_time_invalid_input(self):
        """Teste: trata entradas inválidas."""
        with pytest.raises(ValueError):
            format_seconds_to_time(-1)
        
        with pytest.raises(ValueError):
            format_seconds_to_time("invalid")


class TestValidateUserId:
    """Testes para função validate_user_id."""

    def test_validate_user_id_valid_18_digits(self):
        """Teste: valida IDs de 18 dígitos."""
        assert validate_user_id("123456789012345678") is True
        assert validate_user_id("999999999999999999") is True
        assert validate_user_id("000000000000000000") is True

    def test_validate_user_id_valid_19_digits(self):
        """Teste: valida IDs de 19 dígitos."""
        assert validate_user_id("1234567890123456789") is True
        assert validate_user_id("9999999999999999999") is True

    def test_validate_user_id_invalid_length(self):
        """Teste: rejeita IDs com comprimento inválido."""
        assert validate_user_id("12345678901234567") is False  # 17 dígitos
        assert validate_user_id("12345678901234567890") is False  # 20 dígitos
        assert validate_user_id("") is False  # vazio

    def test_validate_user_id_invalid_characters(self):
        """Teste: rejeita IDs com caracteres não numéricos."""
        assert validate_user_id("12345678901234567a") is False
        assert validate_user_id("12345678901234567-") is False
        assert validate_user_id("12345678901234567 ") is False
        assert validate_user_id("12345678901234567$") is False

    def test_validate_user_id_non_string_input(self):
        """Teste: rejeita entradas que não são strings."""
        assert validate_user_id(123456789012345678) is False
        assert validate_user_id(None) is False
        assert validate_user_id([]) is False
        assert validate_user_id({}) is False


class TestValidateSeconds:
    """Testes para função validate_seconds."""

    def test_validate_seconds_valid(self):
        """Teste: valida segundos válidos."""
        assert validate_seconds(0) is True
        assert validate_seconds(1) is True
        assert validate_seconds(3600) is True
        assert validate_seconds(86400) is True

    def test_validate_seconds_invalid(self):
        """Teste: rejeita segundos inválidos."""
        assert validate_seconds(-1) is False
        assert validate_seconds("100") is False
        assert validate_seconds(1.5) is False
        assert validate_seconds(None) is False


class TestSafeInt:
    """Testes para função safe_int."""

    def test_safe_int_valid_conversion(self):
        """Teste: converte strings numéricas válidas."""
        assert safe_int("123") == 123
        assert safe_int("0") == 0
        assert safe_int("-456") == -456

    def test_safe_int_invalid_conversion(self):
        """Teste: retorna valor padrão para conversão inválida."""
        assert safe_int("invalid") == 0
        assert safe_int("123abc") == 0
        assert safe_int("") == 0
        assert safe_int(None) == 0

    def test_safe_int_custom_default(self):
        """Teste: usa valor padrão personalizado."""
        assert safe_int("invalid", 999) == 999
        assert safe_int("", -1) == -1


class TestSafeIntConversion:
    """Testes para função safe_int_conversion."""

    def test_safe_int_conversion_valid(self):
        """Teste: converte strings numéricas válidas."""
        assert safe_int_conversion("123") == 123
        assert safe_int_conversion("0") == 0
        assert safe_int_conversion("-456") == -456

    def test_safe_int_conversion_invalid_string(self):
        """Teste: levanta ValueError para strings inválidas."""
        with pytest.raises(ValueError, match="Não é possível converter 'invalid' para inteiro"):
            safe_int_conversion("invalid")
        
        with pytest.raises(ValueError, match="Não é possível converter '' para inteiro"):
            safe_int_conversion("")

    def test_safe_int_conversion_non_string(self):
        """Teste: levanta TypeError para entradas não-string."""
        with pytest.raises(TypeError, match="O valor deve ser uma string"):
            safe_int_conversion(123)
        
        with pytest.raises(TypeError, match="O valor deve ser uma string"):
            safe_int_conversion(None)


class TestValidateAndConvertUserId:
    """Testes para função validate_and_convert_user_id."""

    def test_validate_and_convert_user_id_valid(self):
        """Teste: valida e converte IDs válidos."""
        assert validate_and_convert_user_id("123456789012345678") == 123456789012345678
        assert validate_and_convert_user_id("999999999999999999") == 999999999999999999

    def test_validate_and_convert_user_id_19_digits(self):
        """Teste: valida e converte IDs de 19 dígitos."""
        assert validate_and_convert_user_id("1234567890123456789") == 1234567890123456789
        assert validate_and_convert_user_id("9999999999999999999") == 9999999999999999999

    def test_validate_and_convert_user_id_invalid_format(self):
        """Teste: levanta ValueError para formatos inválidos."""
        with pytest.raises(ValueError, match="Formato de user_id inválido"):
            validate_and_convert_user_id("12345678901234567")  # 17 dígitos

        with pytest.raises(ValueError, match="Formato de user_id inválido"):
            validate_and_convert_user_id("12345678901234567a")  # caractere inválido

    def test_validate_and_convert_user_id_non_string(self):
        """Teste: levanta TypeError para entradas não-string."""
        with pytest.raises(TypeError, match="user_id deve ser uma string"):
            validate_and_convert_user_id(123456789012345678)

        with pytest.raises(TypeError, match="user_id deve ser uma string"):
            validate_and_convert_user_id(None)


class TestTruncateString:
    """Testes para função truncate_string."""

    def test_truncate_string_within_limit(self):
        """Teste: não trunca strings dentro do limite."""
        text = "Texto curto"
        assert truncate_string(text, 50) == text
        assert truncate_string(text, 100) == text

    def test_truncate_string_exceeds_limit(self):
        """Teste: trunca strings que excedem o limite."""
        long_text = "Este é um texto muito longo que deve ser truncado"
        truncated = truncate_string(long_text, 20)

        assert len(truncated) == 20
        assert truncated.endswith("...")
        # Prefixo tem 17 caracteres (20 - 3 do sufixo "...")
        assert truncated.startswith("Este é um texto m")

    def test_truncate_string_custom_suffix(self):
        """Teste: usa sufixo personalizado."""
        text = "Texto muito longo para o limite"
        truncated = truncate_string(text, 15, suffix="[...]")

        assert len(truncated) == 15
        assert truncated.endswith("[...]")
        # Prefixo tem 10 caracteres (15 - 5 do sufixo "[...]")
        assert truncated.startswith("Texto muit")

    def test_truncate_string_non_string_input(self):
        """Teste: trata entradas não-string."""
        assert truncate_string(123, 10) == ""
        assert truncate_string(None, 10) == ""
        assert truncate_string([], 10) == ""

    def test_truncate_string_empty_string(self):
        """Teste: trata string vazia."""
        assert truncate_string("", 10) == ""


class TestSetupLogger:
    """Testes para função setup_logger."""

    def test_setup_logger_basic(self):
        """Teste: cria logger básico."""
        logger = setup_logger("test_logger_basic")

        assert logger.name == "test_logger_basic"
        assert logger.level == 20  # logging.INFO = 20

    def test_setup_logger_custom_level(self):
        """Teste: cria logger com nível personalizado."""
        logger = setup_logger("test_logger_level", level=10)  # logging.DEBUG = 10

        assert logger.level == 10

    def test_setup_logger_with_file(self, tmp_path):
        """Teste: cria logger com handler de arquivo."""
        log_file = tmp_path / "test.log"
        logger = setup_logger("test_logger_file", log_file=str(log_file))

        # Verificar que o handler de arquivo foi adicionado
        file_handlers = [h for h in logger.handlers if hasattr(h, 'baseFilename')]
        assert len(file_handlers) == 1

    def test_setup_logger_no_duplicate_handlers(self):
        """Teste: evita handlers duplicados."""
        logger = setup_logger("test_logger_dup")
        initial_handler_count = len(logger.handlers)

        # Configurar novamente o mesmo logger
        setup_logger("test_logger_dup")

        # O número de handlers deve ser o mesmo
        assert len(logger.handlers) == initial_handler_count