"""
Comandos do bot Discord de ranking de atividade.

Este modulo implementa os comandos disponiveis para os usuarios,
incluindo o comando !rankingvideo conforme RF04 e secao 4.4.3 do PRD.
"""

import asyncio
import discord
from discord.ext import commands
from typing import List, Tuple, Optional, Union

from config import EMBED_COLOR, MAX_RANKING_SIZE
from database import load_data
from utils import fetch_user, format_seconds_to_time, truncate_string


async def ranking_video(ctx: commands.Context) -> None:
    """
    Comando !rankingvideo - Exibe o top 10 usuarios por tempo com camera.

    Conforme RF04 e secao 6.1 do PRD:
    - Exibe top 10 usuarios por tempo com camera
    - Formato: Embed Discord com estilizacao
    - Informacoes: posicao, nome/avatar, tempo total (Xh Ymin), numero de sessoes
    - Ordenacao: Decrescente por total_seconds
    - Resposta quando vazio: Mensagem amigavel

    Args:
        ctx: Contexto do comando Discord

    Example:
        >>> !rankingvideo
        # Exibe embed com o ranking
    """
    # Carregar dados do JSON
    data = load_data()

    # Verificar se ha dados (RF04 - caso vazio)
    if not data:
        empty_message = (
            "🎥 **Ranking - Tempo com Câmera Ligada**\n\n"
            "Ainda não há dados de sessões registradas.\n"
            "Seja o primeiro a ligar a câmera! 📹"
        )
        await ctx.send(empty_message)
        return

    # Ordenar por total_seconds decrescente e pegar top 10
    sorted_users: List[Tuple[str, int]] = sorted(
        data.items(),
        key=lambda item: item[1]["total_seconds"],
        reverse=True
    )[:MAX_RANKING_SIZE]

    # Criar embed com cor #5865F2 (Azul Discord)
    embed = discord.Embed(
        title="🎥 Ranking - Tempo com Câmera Ligada",
        color=EMBED_COLOR
    )

    # Adicionar campos para cada usuario no ranking
    guild = ctx.guild

    # Buscar todos os membros em paralelo usando asyncio.gather
    # Isso melhora performance de ~2-5s para ~200-500ms (conforme Task 2)
    member_tasks = [
        fetch_user(guild, user_id)
        for user_id, _ in sorted_users[:MAX_RANKING_SIZE]
    ]
    members = await asyncio.gather(*member_tasks, return_exceptions=True)

    # Processar resultados e adicionar campos ao embed
    position = 1
    for idx, (user_data, member) in enumerate(zip(
        [data for _, data in sorted_users[:MAX_RANKING_SIZE]],
        members
    )):
        # Pular se member é None ou Exception (RNF06)
        if member is None or isinstance(member, Exception):
            continue

        # Formatar tempo
        total_time = format_seconds_to_time(user_data["total_seconds"])
        sessions = user_data["sessions"]

        # Criar nome do usuario com posicao
        name = f"#{position} {member.display_name}"
        name = truncate_string(name, 50)

        # Criar valor com tempo e sessoes
        value = f"⏱️ {total_time}\n📹 {sessions} sessão(ões)"

        # Adicionar campo ao embed
        embed.add_field(
            name=name,
            value=value,
            inline=False
        )

        position += 1

    # Adicionar rodape com informacoes do servidor
    embed.set_footer(
        text=f"Servidor: {guild.name} | Total de {len(data)} usuários registrados"
    )

    # Adicionar thumbnail com icone do servidor se disponivel
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    # Enviar embed
    await ctx.send(embed=embed)


# Configurar comandos para o bot
def setup_commands(bot: commands.Bot) -> None:
    """
    Registra os comandos do bot.

    Args:
        bot: Instancia do bot Discord
    """
    bot.command(name="rankingvideo")(ranking_video)
