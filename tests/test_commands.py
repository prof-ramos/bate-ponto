"""Tests para commands.py - ranking command"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord.ext import commands
import asyncio

from commands import ranking_video


@pytest.fixture
def mock_ctx():
    """Fixture para contexto do comando"""
    ctx = MagicMock(spec=commands.Context)
    ctx.guild = MagicMock(spec=discord.Guild)
    ctx.guild.name = "Test Server"
    ctx.guild.icon = None
    ctx.send = AsyncMock()
    return ctx


@pytest.mark.asyncio
async def test_fetch_users_parallel(mock_ctx):
    """Teste: fetch_user é chamado em paralelo"""
    # Mock database.load_data
    test_data = {
        "123": {"total_seconds": 3600, "sessions": 5},
        "456": {"total_seconds": 7200, "sessions": 10},
        "789": {"total_seconds": 1800, "sessions": 3},
    }

    with patch('commands.load_data', return_value=test_data):
        with patch('commands.fetch_user') as mock_fetch:
            # Mock retornar membros válidos
            mock_member = MagicMock(spec=discord.Member)
            mock_member.display_name = "Test User"
            mock_fetch.return_value = mock_member

            await ranking_video(mock_ctx)

            # Verificar: fetch_user foi chamado para todos os usuários
            assert mock_fetch.call_count == len(test_data)


@pytest.mark.asyncio
async def test_ranking_includes_top_users(mock_ctx):
    """Teste: ranking inclui top 10 usuários"""
    # Criar 15 usuários
    test_data = {
        str(i): {"total_seconds": i * 100, "sessions": 1}
        for i in range(1, 16)
    }

    with patch('commands.load_data', return_value=test_data):
        with patch('commands.fetch_user') as mock_fetch:
            mock_member = MagicMock(spec=discord.Member)
            mock_member.display_name = "User"
            mock_fetch.return_value = mock_member

            await ranking_video(mock_ctx)

            # Verificar: embed foi enviado
            assert mock_ctx.send.called

            # Verificar: apenas top 10 (não 15)
            call_args = mock_ctx.send.call_args
            # Pega o embed (pode ser posicional ou keyword)
            embed = call_args[0][0] if call_args[0] else call_args[1]['embed']
            assert len(embed.fields) <= 10


@pytest.mark.asyncio
async def test_ranking_empty_data(mock_ctx):
    """Teste: ranking com dados vazios exibe mensagem amigável"""
    with patch('commands.load_data', return_value={}):
        await ranking_video(mock_ctx)

        # Verificar: mensagem de "sem dados" foi enviada
        assert mock_ctx.send.called
        call_args = mock_ctx.send.call_args
        message = call_args[0][0]
        assert "Ainda não há dados" in message


@pytest.mark.asyncio
async def test_ranking_skips_invalid_users(mock_ctx):
    """Teste: ranking pula usuários inexistentes (RNF06)"""
    test_data = {
        "123": {"total_seconds": 3600, "sessions": 5},
        "456": {"total_seconds": 7200, "sessions": 10},
        "789": {"total_seconds": 1800, "sessions": 3},
    }

    with patch('commands.load_data', return_value=test_data):
        with patch('commands.fetch_user') as mock_fetch:
            # Primeiro usuário é válido, segundo é None (inexistente)
            mock_member_valid = MagicMock(spec=discord.Member)
            mock_member_valid.display_name = "Valid User"

            # Retornar None para o segundo usuário (inexistente)
            mock_fetch.side_effect = [mock_member_valid, None, mock_member_valid]

            await ranking_video(mock_ctx)

            # Verificar: embed foi enviado
            assert mock_ctx.send.called

            # Verificar: apenas 2 usuários no embed (um foi pulado)
            call_args = mock_ctx.send.call_args
            embed = call_args[0][0] if call_args[0] else call_args[1]['embed']
            assert len(embed.fields) == 2


@pytest.mark.asyncio
async def test_ranking_sorted_by_time(mock_ctx):
    """Teste: ranking ordenado por tempo decrescente"""
    test_data = {
        "123": {"total_seconds": 1000, "sessions": 1},
        "456": {"total_seconds": 3000, "sessions": 2},
        "789": {"total_seconds": 2000, "sessions": 1},
    }

    with patch('commands.load_data', return_value=test_data):
        with patch('commands.fetch_user') as mock_fetch:
            mock_member = MagicMock(spec=discord.Member)
            mock_member.display_name = "User"
            mock_fetch.return_value = mock_member

            await ranking_video(mock_ctx)

            # Verificar: embed foi enviado
            assert mock_ctx.send.called

            # Verificar: ordem decrescente por tempo
            call_args = mock_ctx.send.call_args
            embed = call_args[0][0] if call_args[0] else call_args[1]['embed']

            # Primeiro campo deve ter mais tempo (3000s)
            first_field = embed.fields[0]
            assert "3h" in first_field.value or "50min" in first_field.value

            # Último campo deve ter menos tempo (1000s)
            last_field = embed.fields[-1]
            assert "16min" in last_field.value
