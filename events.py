"""
events.py - Event handlers para o bot Discord de ranking de atividade.

Este módulo contém os handlers de eventos do Discord, focando principalmente
no rastreamento de câmera ligada através de on_voice_state_update.

Seção 4.4.1 do PRD: Event Handler - Voice State
"""

from database import update_video_time
import logging
import asyncio
from datetime import datetime
from typing import Dict, Optional

import discord
from discord.ext import commands

# Configuração de logging conforme seção 6.2 do PRD
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoSessionManager:
    """Gerenciador de sessões de vídeo com proteção de concorrência

    Gerencia sessões de vídeo ativas com asyncio.Lock() para prevenir
    race conditions quando múltiplos toggles de câmera ocorrem simultaneamente.

    Estrutura interna:
        _sessions: Dict[str, datetime] = {"user_id": datetime_object}
    """

    def __init__(self):
        self._sessions: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()

    async def start_session(self, user_id: str, timestamp: datetime) -> None:
        """Inicia sessão de vídeo para usuário

        Args:
            user_id: ID do usuário Discord como string
            timestamp: Timestamp de início da sessão
        """
        async with self._lock:
            self._sessions[user_id] = timestamp

    async def end_session(self, user_id: str) -> Optional[datetime]:
        """Finaliza sessão e retorna timestamp de início

        Args:
            user_id: ID do usuário Discord como string

        Returns:
            Timestamp de início da sessão ou None se não existir
        """
        async with self._lock:
            return self._sessions.pop(user_id, None)

    def has_session(self, user_id: str) -> bool:
        """Verifica se usuário tem sessão ativa

        Nota: Este método não usa lock pois é apenas para verificação.
        Para operações que modificam o estado, use start_session/end_session.

        Args:
            user_id: ID do usuário Discord como string

        Returns:
            True se usuário tem sessão ativa, False caso contrário
        """
        return user_id in self._sessions

    def clear(self) -> None:
        """Remove todas as sessões ativas

        Nota: Método síncrono para uso em testes.
        Em produção, considere adicionar versão async com lock.
        """
        self._sessions.clear()

    @property
    def sessions(self) -> Dict[str, datetime]:
        """Retorna cópia das sessões (para compatibilidade com testes)

        Returns:
            Cópia do dict de sessões ativas
        """
        return self._sessions.copy()


# Instância global do gerenciador de sessões
active_video_sessions = VideoSessionManager()


async def on_voice_state_update(
    member: discord.Member,
    before: discord.VoiceState,
    after: discord.VoiceState
) -> None:
    """
    Handler para mudanças no estado de voz dos membros.

    Detecta mudanças em self_video e rastreia tempo de câmera ligada.

    Args:
        member: O membro do Discord cujo estado mudou
        before: Estado de voz anterior
        after: Estado de voz atual

    Comportamento (UC01/UC02 - seção 5 do PRD):
        1. Detecta self_video = True -> Salva timestamp
        2. Detecta self_video = False -> Calcula duração -> Atualiza JSON
    """
    # Detecta quando usuário liga a câmera (UC01)
    if not before.self_video and after.self_video:
        user_id = str(member.id)
        await active_video_sessions.start_session(user_id, datetime.now())

        # Log conforme seção 6.2 do PRD
        logger.info(f"📹 {member.display_name} ligou a câmera")

    # Detecta quando usuário desliga a câmera (UC02)
    elif before.self_video and not after.self_video:
        user_id = str(member.id)

        # Finaliza sessão e obtém timestamp de início
        start_time = await active_video_sessions.end_session(user_id)
        if start_time:
            # Calcula duração da sessão
            duration = datetime.now() - start_time
            duration_seconds = int(duration.total_seconds())

            # Atualiza dados persistentes via database.py
            update_video_time(user_id, duration_seconds)

            # Log conforme seção 6.2 do PRD
            logger.info(f"📹 {member.display_name} desligou - {duration_seconds}s gravados")


def setup(bot: commands.Bot) -> None:
    """
    Registra os event handlers no bot.

    Args:
        bot: Instância do bot Discord
    """
    bot.add_listener(on_voice_state_update, 'on_voice_state_update')


# Type hints para todos os componentes (RNF10)
__all__ = [
    'active_video_sessions',
    'on_voice_state_update',
    'setup',
]
