"""
events.py - Event handlers para o bot Discord de ranking de atividade.

Este módulo contém os handlers de eventos do Discord, focando principalmente
no rastreamento de câmera ligada através de on_voice_state_update.

Seção 4.4.1 do PRD: Event Handler - Voice State
"""

import logging
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

# Estrutura de sessões ativas conforme RF07 do PRD
# active_video_sessions = {
#     "user_id": datetime_object
# }
active_video_sessions: Dict[str, datetime] = {}


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
        active_video_sessions[user_id] = datetime.now()

        # Log conforme seção 6.2 do PRD
        logger.info(f"📹 {member.display_name} ligou a câmera")

    # Detecta quando usuário desliga a câmera (UC02)
    elif before.self_video and not after.self_video:
        user_id = str(member.id)

        # Verifica se há sessão ativa para este usuário
        if user_id in active_video_sessions:
            # Calcula duração da sessão
            start_time = active_video_sessions[user_id]
            duration = datetime.now() - start_time
            duration_seconds = int(duration.total_seconds())

            # Remove sessão ativa
            del active_video_sessions[user_id]

            # Atualiza dados persistentes via database.py
            _update_video_time(user_id, duration_seconds)

            # Log conforme seção 6.2 do PRD
            logger.info(f"📹 {member.display_name} desligou - {duration_seconds}s gravados")


def _update_video_time(user_id: str, duration: int) -> None:
    """
    Atualiza o tempo de vídeo do usuário no JSON.

    Função stub que será substituída pela implementação em database.py.
    Mantida aqui para permitir que events.py funcione de forma autônoma.

    Args:
        user_id: ID do usuário Discord como string
        duration: Duração da sessão em segundos

    Note:
        Esta função será removida quando database.py for implementado,
        pois a funcionalidade será importada de lá.
    """
    import json
    import os
    from pathlib import Path

    json_path = Path(__file__).parent / "video_ranking.json"

    # Carrega dados existentes
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}

    # Atualiza dados do usuário
    if user_id not in data:
        data[user_id] = {"total_seconds": 0, "sessions": 0}

    data[user_id]["total_seconds"] += duration
    data[user_id]["sessions"] += 1

    # Salva dados atualizados (indent=2 conforme RNF12)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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
