"""Tests para utils.py - funções utilitárias."""
import pytest
import logging
from pathlib import Path
from utils import (
    format_seconds_to_time,
    validate_user_id,
    validate_seconds,
    setup_logger,
    safe_int,
    truncate_string
)


class TestFormatSecondsToTime:
    """Testes para função format_seconds_to_time."""

    def test_format_seconds_only(self):
        """Teste: formata segundos puros (< 1 minuto)."""
        assert format_seconds_to_time(0) == "0s"
        assert format_seconds_to_time(30) == "30s"
        assert format_seconds_to_time(59) == "59s"

    def test_format_minutes_only(self):
        """Teste: formata minutos puros (< 1 hora)."""
        assert format_seconds_to_time(60) == "1min"
        assert format_seconds_to_time(300) == "5min"
        assert format_seconds_to_time(3599) == "59min"

    def test_format_hours_only(self):
        """Teste: formata horas exatas (sem minutos restantes)."""
        assert format_seconds_to_time(3600) == "1h"
        assert format_seconds_to_time(7200) == "2h"
        assert format_seconds_to_time(10800) == "3h"

    def test_format_hours_and_minutes(self):
        """Teste: formata horas com minutos."""
        assert format_seconds_to_time(3660) == "1h 1min"
        assert format_seconds_to_time(5400) == "1h 30min"
        assert format_seconds_to_time(3665) == "1h 1min"
        assert format_seconds_to_time(7261) == "2h 1min"

    def test_format_large_durations(self):
        """Teste: formata durações grandes."""
        # 24 horas
        assert format_seconds_to_time(86400) == "24h"
        # 25h 30min
        assert format_seconds_to_time(91800) == "25h 30min"
        # 100h
        assert format_seconds_to_time(360000) == "100h"

    def test_format_rejects_negative(self):
        """Teste: rejeita valores negativos."""
        with pytest.raises(ValueError, match="seconds deve ser um inteiro nao-negativo"):
            format_seconds_to_time(-1)

    def test_format_rejects_non_integer(self):
        """Teste: rejeita valores não-inteiros."""
        with pytest.raises(ValueError, match="seconds deve ser um inteiro nao-negativo"):
            format_seconds_to_time(30.5)
        with pytest.raises(ValueError, match="seconds deve ser um inteiro nao-negativo"):
            format_seconds_to_time("30")


class TestValidateUserId:
    """Testes para função validate_user_id."""

    def test_valid_snowflake_ids(self):
        """Teste: aceita IDs Discord válidos (18-19 dígitos)."""
        assert validate_user_id("123456789012345678") is True  # 18 dígitos
        assert validate_user_id("1234567890123456789") is True  # 19 dígitos

    def test_invalid_too_short(self):
        """Teste: rejeita IDs muito curtos."""
        assert validate_user_id("12345") is False
        assert validate_user_id("12345678901234567") is False  # 17 dígitos

    def test_invalid_too_long(self):
        """Teste: rejeita IDs muito longos."""
        assert validate_user_id("12345678901234567890") is False  # 20 dígitos

    def test_invalid_non_numeric(self):
        """Teste: rejeita IDs não-numéricos."""
        assert validate_user_id("abcdefghijklmnop") is False
        assert validate_user_id("12345678901234567a") is False
        assert validate_user_id("abc123456789012345") is False

    def test_invalid_type(self):
        """Teste: rejeita tipos não-string."""
        assert validate_user_id(123456789012345678) is False
        assert validate_user_id(None) is False
        assert validate_user_id([]) is False

    def test_empty_string(self):
        """Teste: rejeita string vazia."""
        assert validate_user_id("") is False


class TestValidateSeconds:
    """Testes para função validate_seconds."""

    def test_valid_seconds(self):
        """Teste: aceita segundos válidos."""
        assert validate_seconds(0) is True
        assert validate_seconds(1) is True
        assert validate_seconds(3600) is True
        assert validate_seconds(999999) is True

    def test_invalid_negative(self):
        """Teste: rejeita valores negativos."""
        assert validate_seconds(-1) is False
        assert validate_seconds(-100) is False

    def test_invalid_type(self):
        """Teste: rejeita tipos não-inteiros."""
        assert validate_seconds(30.5) is False
        assert validate_seconds("30") is False
        assert validate_seconds(None) is False
        assert validate_seconds([]) is False


class TestSetupLogger:
    """Testes para função setup_logger."""

    def test_creates_logger_with_name(self):
        """Teste: cria logger com nome especificado."""
        logger = setup_logger("test-logger")
        assert logger.name == "test-logger"

    def test_default_level(self):
        """Teste: usa nível INFO por padrão."""
        logger = setup_logger()
        assert logger.level == logging.INFO

    def test_custom_level(self):
        """Teste: aceita nível personalizado."""
        logger = setup_logger(level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_has_console_handler(self):
        """Teste: possui handler de console."""
        logger = setup_logger()
        assert len(logger.handlers) > 0
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_clears_previous_handlers(self):
        """Teste: limpa handlers anteriores."""
        logger = setup_logger("test-clear")
        first_handler_count = len(logger.handlers)
        logger.handlers.clear()

        # Adicionar handler manualmente
        logger.addHandler(logging.StreamHandler())

        # Chamar setup_logger novamente
        logger = setup_logger("test-clear")

        # Deve ter apenas um handler (o novo)
        assert len(logger.handlers) == 1

    def test_log_output(self, caplog):
        """Teste: gera logs corretamente."""
        logger = setup_logger("test-output")

        with caplog.at_level(logging.INFO):
            logger.info("Test message")

        assert "Test message" in caplog.text


class TestSafeInt:
    """Testes para função safe_int."""

    def test_converts_valid_string(self):
        """Teste: converte string válida para int."""
        assert safe_int("123") == 123
        assert safe_int("0") == 0
        assert safe_int("-456") == -456

    def test_returns_default_for_invalid_string(self):
        """Teste: retorna default para string inválida."""
        assert safe_int("abc") == 0
        assert safe_int("123abc") == 0

    def test_returns_default_for_none(self):
        """Teste: retorna default para None."""
        assert safe_int(None) == 0

    def test_custom_default(self):
        """Teste: usa default personalizado."""
        assert safe_int("invalid", default=-1) == -1
        assert safe_int(None, default=999) == 999

    def test_handles_numeric_types(self):
        """Teste: lida com tipos numéricos."""
        assert safe_int(123) == 123
        assert safe_int(123.45) == 123


class TestTruncateString:
    """Testes para função truncate_string."""

    def test_returns_short_string_unchanged(self):
        """Teste: retorna string curta inalterada."""
        assert truncate_string("hello") == "hello"
        assert truncate_string("a" * 50) == "a" * 50

    def test_truncates_long_string(self):
        """Teste: trunca string longa."""
        long_text = "a" * 100
        result = truncate_string(long_text, max_length=50)
        assert len(result) == 50
        assert result.endswith("...")

    def test_custom_suffix(self):
        """Teste: usa sufixo personalizado."""
        long_text = "a" * 100
        result = truncate_string(long_text, max_length=50, suffix=">>")
        assert len(result) == 50
        assert result.endswith(">>")

    def test_handles_non_string(self):
        """Teste: retorna vazio para não-string."""
        assert truncate_string(123) == ""
        assert truncate_string(None) == ""
        assert truncate_string([]) == ""

    def test_preserves_content(self):
        """Teste: preserva conteúdo antes do truncamento."""
        text = "The quick brown fox jumps over the lazy dog"
        result = truncate_string(text, max_length=20)
        assert result.startswith("The quick")

    def test_unicode_handling(self):
        """Teste: lida com caracteres Unicode."""
        text = "João São Paulo Brasil é muito grande"
        result = truncate_string(text, max_length=20)
        assert len(result) == 20
        assert result.endswith("...")


class TestIntegrationUtils:
    """Testes de integração entre funções utilitárias."""

    def test_format_and_validate_workflow(self):
        """Teste: workflow completo de validação e formatação."""
        # Validar segundos
        assert validate_seconds(3665) is True

        # Formatar
        formatted = format_seconds_to_time(3665)
        assert formatted == "1h 1min"

    def test_user_id_validation_chain(self):
        """Teste: cadeia de validação de user ID."""
        valid_ids = [
            "123456789012345678",
            "987654321098765432",
            "111111111111111111"
        ]

        for user_id in valid_ids:
            assert validate_user_id(user_id) is True
            assert safe_int(user_id, default=0) != 0
