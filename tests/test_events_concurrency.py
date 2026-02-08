"""Tests de concorrência para events.py"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import MagicMock
import discord

from events import on_voice_state_update, active_video_sessions


@pytest.fixture
def mock_member():
    """Fixture para member do Discord"""
    member = MagicMock(spec=discord.Member)
    member.id = 123456789012345678
    member.display_name = "Test User"
    return member


@pytest.fixture(autouse=True)
def clear_sessions():
    """Limpa sessões antes e depois de cada teste"""
    active_video_sessions.clear()
    yield
    active_video_sessions.clear()


@pytest.mark.asyncio
async def test_concurrent_camera_toggle_safe(mock_member):
    """Teste: múltiplos toggle de câmera simultâneos são seguros"""
    # Criar estados de voz mock
    before_on = MagicMock(spec=discord.VoiceState)
    after_on = MagicMock(spec=discord.VoiceState)
    before_on.self_video = False
    after_on.self_video = True

    before_off = MagicMock(spec=discord.VoiceState)
    after_off = MagicMock(spec=discord.VoiceState)
    before_off.self_video = True
    after_off.self_video = False

    # Simular 10 toggle simultâneos do mesmo usuário
    tasks = []
    for _ in range(10):
        tasks.append(on_voice_state_update(mock_member, before_on, after_on))
        tasks.append(on_voice_state_update(mock_member, before_off, after_off))

    # Executar todos simultaneamente
    await asyncio.gather(*tasks)

    # Verificar: estado consistente (sem exceções)
    # Com lock: sempre passa
    # Sem lock: pode falhar com KeyError durante operações concorrentes
    assert True  # Se chegou aqui, não houve exceção de concorrência


@pytest.mark.asyncio
async def test_concurrent_multiple_users(mock_member):
    """Teste: múltiplos usuários ligando/desligando câmera simultaneamente"""
    # Criar múltiplos membros mock
    members = []
    for i in range(5):
        member = MagicMock(spec=discord.Member)
        member.id = 123456789012345678 + i
        member.display_name = f"Test User {i}"
        members.append(member)

    # Criar estados de voz mock
    before_on = MagicMock(spec=discord.VoiceState)
    after_on = MagicMock(spec=discord.VoiceState)
    before_on.self_video = False
    after_on.self_video = True

    before_off = MagicMock(spec=discord.VoiceState)
    after_off = MagicMock(spec=discord.VoiceState)
    before_off.self_video = True
    after_off.self_video = False

    # Simular todos ligando câmera simultaneamente
    on_tasks = [on_voice_state_update(member, before_on, after_on) for member in members]
    await asyncio.gather(*on_tasks)

    # Verificar que todos têm sessões ativas
    for member in members:
        assert active_video_sessions.has_session(str(member.id))

    # Simular todos desligando câmera simultaneamente
    off_tasks = [on_voice_state_update(member, before_off, after_off) for member in members]
    await asyncio.gather(*off_tasks)

    # Verificar que ninguém mais tem sessão ativa
    for member in members:
        assert not active_video_sessions.has_session(str(member.id))


@pytest.mark.asyncio
async def test_start_session_isolation(mock_member):
    """Teste: start_session é isolado por lock"""
    user_id = str(mock_member.id)

    # Criar múltiplas tarefas de start_session simultâneas
    tasks = []
    for _ in range(10):
        timestamp = datetime.now()
        tasks.append(active_video_sessions.start_session(user_id, timestamp))

    # Executar todas simultaneamente
    await asyncio.gather(*tasks)

    # Verificar: apenas um timestamp existe (sobrescrita é segura com lock)
    sessions = active_video_sessions.sessions
    assert user_id in sessions
    assert isinstance(sessions[user_id], datetime)


@pytest.mark.asyncio
async def test_end_session_isolation(mock_member):
    """Teste: end_session é isolado por lock"""
    user_id = str(mock_member.id)

    # Setup: criar sessão
    await active_video_sessions.start_session(user_id, datetime.now())

    # Criar múltiplas tarefas de end_session simultâneas
    tasks = []
    for _ in range(10):
        tasks.append(active_video_sessions.end_session(user_id))

    # Executar todas simultaneamente
    results = await asyncio.gather(*tasks)

    # Verificar: apenas uma retorna o timestamp, as outras retornam None
    # (pois pop é thread-safe com lock)
    non_none_results = [r for r in results if r is not None]
    assert len(non_none_results) == 1
    assert isinstance(non_none_results[0], datetime)

    # Verificar que sessão foi removida
    assert not active_video_sessions.has_session(user_id)
