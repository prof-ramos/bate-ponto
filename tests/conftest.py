"""Configuração e fixtures compartilhadas para testes."""
import pytest
from unittest.mock import MagicMock, AsyncMock
import discord
from pathlib import Path
import tempfile
import os
import sys


# Adicionar diretório raiz ao path para importar módulos do projeto
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_guild():
    """Fixture para Guild do Discord."""
    guild = MagicMock(spec=discord.Guild)
    guild.id = 123456789012345678
    guild.name = "Test Server"
    return guild


@pytest.fixture
def mock_member():
    """Fixture para Member do Discord."""
    member = MagicMock(spec=discord.Member)
    member.id = 987654321098765432
    member.display_name = "Test User"
    member.name = "testuser"
    member.guild = mock_guild()
    return member


@pytest.fixture
def mock_voice_state():
    """Fixture para VoiceState do Discord."""
    voice_state = MagicMock(spec=discord.VoiceState)
    voice_state.self_video = False
    voice_state.channel = MagicMock(spec=discord.VoiceChannel)
    voice_state.channel.id = 111222333444555666
    return voice_state


@pytest.fixture
def temp_data_file():
    """Fixture que cria um arquivo JSON temporário para testes de database."""
    # Salvar o caminho original do DATA_FILE
    from database import DATA_FILE as original_data_file
    import database

    # Criar arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_path = f.name
        f.write("{}")

    # Substituir DATA_FILE pelo temporário
    database.DATA_FILE = Path(temp_path)

    yield Path(temp_path)

    # Cleanup: restaurar original e deletar temporário
    database.DATA_FILE = original_data_file
    if Path(temp_path).exists():
        Path(temp_path).unlink()


@pytest.fixture
def sample_data():
    """Dados de exemplo para testes."""
    return {
        "123456789012345678": {
            "total_seconds": 3600,
            "sessions": 5
        },
        "987654321098765432": {
            "total_seconds": 7200,
            "sessions": 10
        },
        "111111111111111111": {
            "total_seconds": 1800,
            "sessions": 3
        }
    }
