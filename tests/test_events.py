"""Tests para events.py - voice state handler"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import discord

from events import on_voice_state_update, active_video_sessions


@pytest.fixture
def mock_member():
    """Fixture para member do Discord"""
    member = MagicMock(spec=discord.Member)
    member.id = 123456789012345678
    member.display_name = "Test User"
    return member


@pytest.fixture
def mock_voice_states():
    """Fixture para estados de voz"""
    before = MagicMock(spec=discord.VoiceState)
    after = MagicMock(spec=discord.VoiceState)
    return before, after


@pytest.mark.asyncio
async def test_camera_on_registers_session(mock_member, mock_voice_states):
    """Teste: ligar câmera registra sessão ativa"""
    before, after = mock_voice_states
    before.self_video = False
    after.self_video = True

    # Limpar sessões ativas
    active_video_sessions.clear()

    await on_voice_state_update(mock_member, before, after)

    # Verificar que sessão foi registrada
    assert str(mock_member.id) in active_video_sessions
    assert isinstance(active_video_sessions[str(mock_member.id)], datetime)


@pytest.mark.asyncio
async def test_camera_off_updates_database(mock_member, mock_voice_states):
    """Teste: desligar câmera chama database.update_video_time()"""
    before, after = mock_voice_states
    before.self_video = True
    after.self_video = False

    # Setup: sessão ativa existe
    active_video_sessions.clear()
    active_video_sessions[str(mock_member.id)] = datetime.now()

    # Mock database.update_video_time onde é importado em events.py
    with patch('events.update_video_time') as mock_update:
        await on_voice_state_update(mock_member, before, after)

        # Verificar que update_video_time foi chamado
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[0][0] == str(mock_member.id)  # user_id
        assert isinstance(call_args[0][1], int)  # duration in seconds


@pytest.mark.asyncio
async def test_camera_off_removes_session(mock_member, mock_voice_states):
    """Teste: desligar câmera remove sessão ativa"""
    before, after = mock_voice_states
    before.self_video = True
    after.self_video = False

    # Setup: sessão ativa existe
    active_video_sessions.clear()
    user_id = str(mock_member.id)
    active_video_sessions[user_id] = datetime.now()

    with patch('events.update_video_time'):
        await on_voice_state_update(mock_member, before, after)

        # Verificar que sessão foi removida
        assert user_id not in active_video_sessions
