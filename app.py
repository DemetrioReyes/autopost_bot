import asyncio

from bot.commands import registrar_comandos
from bot.config import DISCORD_TOKEN, bot
from bot.events import registrar_eventos
from bot.reminder import iniciar_recordatorios


async def main():
    async with bot:
        registrar_comandos(bot)
        registrar_eventos(bot)
        iniciar_recordatorios(bot)
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
