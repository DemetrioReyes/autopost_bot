import asyncio

import discord
import requests

from .config import waiting_for_input
from .storage import guardar_channel
from .utils import es_url, limpiar_html
from .views import crear_tono_view


def registrar_eventos(bot):
    @bot.event
    async def on_ready():
        await bot.tree.sync()
        print(f"Bot encendido como {bot.user} y esperando ideas...")

    @bot.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return
        if message.author.id in waiting_for_input:
            return
        if not message.content.startswith("!post"):
            return

        texto = message.content[len("!post"):].strip()

        # Detectar imagen adjunta
        imagen_bytes        = None
        imagen_content_type = "image/jpeg"
        for att in message.attachments:
            if att.content_type and att.content_type.startswith("image/"):
                try:
                    loop = asyncio.get_event_loop()
                    r    = await loop.run_in_executor(None, lambda url=att.url: requests.get(url, timeout=15))
                    imagen_bytes        = r.content
                    imagen_content_type = att.content_type.split(";")[0]
                except Exception:
                    pass
                break

        if not texto:
            await message.channel.send(
                "Uso: `!post tu idea aquí` o `!post https://url.com`\n"
                "También puedes adjuntar una imagen al mensaje."
            )
            return

        user_id = message.author.id
        guardar_channel(message.channel.id)

        if es_url(texto):
            await message.channel.send("Leyendo el contenido del enlace...")
            try:
                loop = asyncio.get_event_loop()
                r    = await loop.run_in_executor(
                    None,
                    lambda: requests.get(texto, timeout=10, headers={"User-Agent": "Mozilla/5.0"}),
                )
                r.raise_for_status()
                contenido_limpio = limpiar_html(r.text)[:3500]
                idea = f"Basado en este artículo o página web:\n\n{contenido_limpio}"
            except Exception as e:
                await message.channel.send(f"No pude leer el enlace: `{e!s}`")
                return
            view = crear_tono_view(user_id, idea, url=texto,
                                    imagen_bytes=imagen_bytes, imagen_content_type=imagen_content_type)
        else:
            view = crear_tono_view(user_id, texto,
                                    imagen_bytes=imagen_bytes, imagen_content_type=imagen_content_type)

        nota = " (con imagen adjunta)" if imagen_bytes else ""
        await message.channel.send(f"Elige el tono del post{nota}:", view=view)
