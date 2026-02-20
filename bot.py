#!/usr/bin/env python3
"""
bot.py - Ponto de entrada principal do Bot Discord de Ranking de Atividade.

Este módulo configura e inicializa o bot Discord, registrando eventos e comandos
conforme especificado na seção 4.3 do PRD.
"""

import logging
import sys
from typing import NoReturn

import discord
from discord.ext import commands

# Importar configurações dos módulos
from config import DISCORD_TOKEN, COMMAND_PREFIX, get_intents, setup_logger

# Importar handlers e comandos
from events import on_voice_state_update as voice_handler
from commands import ranking_video

# Configuração de logging
logger = setup_logger(__name__)


def create_bot() -> commands.Bot:
    """
    Cria e configura a instância do bot Discord.

    Configura o bot com:
    - Command prefix do ambiente
    - Intents configurados
    - Event handlers registrados
    - Command handlers registrados
    - Tratamento de erros

    Returns:
        commands.Bot: Instância do bot configurada
    """
    # Criar bot com intents e prefix do config
    bot = commands.Bot(
        command_prefix=COMMAND_PREFIX,
        intents=get_intents(),
        help_command=None  # Desabilita comando de help padrão
    )

    @bot.event
    async def on_ready() -> None:
        """
        Evento chamado quando o bot está conectado e pronto.

        Loga informações de conexão e inicializa sistemas.
        """
        logger.info(f'Bot conectado como {bot.user.name}#{bot.user.discriminator}')
        logger.info(f'ID do bot: {bot.user.id}')
        logger.info(f'Conectado a {len(bot.guilds)} servidores')

        # Configurar status do bot
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name='câmeras ligadas'
            )
        )

    @bot.event
    async def on_voice_state_update(
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> None:
        """
        Evento chamado quando há mudança no estado de voz de um membro.

        Detecta quando usuários ligam/desligam câmera e atualiza o ranking.
        Conforme RF01 do PRD.

        Args:
            member: Membro do Discord que teve mudança de estado
            before: Estado de voz anterior
            after: Novo estado de voz
        """
        try:
            await voice_handler(member, before, after)
        except Exception as e:
            logger.error(f'Erro no handler de voice state: {e}', exc_info=True)

    # Registrar comando de ranking
    @bot.command(name='rankingvideo')
    async def ranking_video_command(ctx: commands.Context) -> None:
        """
        Comando para exibir o ranking de tempo com câmera ligada.

        Conforme RF04 do PRD, exibe top 10 usuários por tempo de câmera.

        Args:
            ctx: Contexto do comando Discord
        """
        try:
            await ranking_video(ctx)
        except Exception as e:
            logger.error(f'Erro no comando rankingvideo: {e}', exc_info=True)
            await ctx.send('Erro ao processar comando. Tente novamente mais tarde.')

    @bot.event
    async def on_command_error(ctx: commands.Context, error: Exception) -> None:
        """
        Evento chamado quando ocorre um erro em um comando.

        Fornece tratamento de erro amigável para o usuário e loga o erro.

        Args:
            ctx: Contexto do comando que falhou
            error: Exceção que causou o erro
        """
        if isinstance(error, commands.CommandNotFound):
            # Ignorar silenciosamente comandos não encontrados
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'Argumento faltando: {error.param.name}')
            return

        if isinstance(error, commands.BadArgument):
            await ctx.send(f'Argumento inválido fornecido.')
            return

        # Logar outros erros
        logger.error(f'Erro no comando {ctx.command}: {error}', exc_info=True)
        await ctx.send('Ocorreu um erro ao executar o comando.')

    return bot


def run_bot() -> NoReturn:
    """
    Inicializa e executa o bot Discord.

    Carrega o token do ambiente, cria o bot e inicia a conexão.
    Implementa shutdown graceful e tratamento de erros críticos.

    Raises:
        SystemExit: Se o token não estiver configurado
    """
    if not DISCORD_TOKEN:
        logger.error('DISCORD_TOKEN não encontrado no arquivo .env')
        logger.error('Crie um arquivo .env baseado no .env.example')
        sys.exit(1)

    bot = create_bot()

    try:
        logger.info('Iniciando bot...')
        bot.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error('Falha na autenticação. Verifique o DISCORD_TOKEN no arquivo .env')
        sys.exit(1)
    except discord.ConnectionClosed as e:
        logger.error(f'Conexão com Discord fechada: {e}')
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info('Bot interrompido pelo usuário')
        sys.exit(0)
    except Exception as e:
        logger.error(f'Erro inesperado ao executar bot: {e}', exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    run_bot()
