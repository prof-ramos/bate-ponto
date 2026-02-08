"""Testes de integração end-to-end"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from discord.ext import commands

from bot import create_bot


@pytest.mark.asyncio
async def test_bot_startup():
    """Teste: bot inicia sem erros"""
    with patch('bot.DISCORD_TOKEN', 'test_token'):
        bot = create_bot()
        assert bot is not None
        assert bot.command_prefix == "!"


@pytest.mark.asyncio
async def test_ranking_command_integration():
    """Teste: comando de ranking funciona end-to-end"""
    ctx = MagicMock(spec=commands.Context)
    ctx.guild = MagicMock()
    ctx.guild.name = "Test Server"
    ctx.guild.icon = None
    ctx.guild.fetch_member = AsyncMock()
    ctx.send = AsyncMock()

    mock_member = MagicMock()
    mock_member.display_name = "Integration Test User"
    ctx.guild.fetch_member.return_value = mock_member

    with patch('commands.load_data') as mock_load:
        mock_load.return_value = {"123": {"total_seconds": 3600, "sessions": 5}}
        from commands import ranking_video
        await ranking_video(ctx)

        assert ctx.send.called
