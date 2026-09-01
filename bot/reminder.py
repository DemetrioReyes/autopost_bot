from datetime import datetime

from discord.ext import tasks

from .config import RECORDATORIO_DIAS
from .linkedin import publicar_en_linkedin
from .storage import (
    cargar_channels,
    cargar_posts,
    cargar_programados,
    eliminar_programado,
)


def iniciar_recordatorios(bot):
    estado = {"ultima_alerta": None}

    # ── Recordatorio de consistencia (cada hora) ──────────────────────────────

    @tasks.loop(hours=1)
    async def recordatorio():
        posts = cargar_posts()
        if not posts:
            return
        ultimo = datetime.fromisoformat(posts[-1]["fecha"])
        dias   = (datetime.now() - ultimo).days
        hoy    = datetime.now().strftime("%Y-%m-%d")
        if dias < RECORDATORIO_DIAS or estado["ultima_alerta"] == hoy:
            return
        estado["ultima_alerta"] = hoy
        for ch_id in cargar_channels():
            try:
                channel = bot.get_channel(ch_id)
                if channel:
                    await channel.send(
                        f"Llevas **{dias} días** sin publicar en LinkedIn.\n"
                        "Envíame una idea para crear un post."
                    )
            except Exception:
                pass

    @recordatorio.before_loop
    async def before_recordatorio():
        await bot.wait_until_ready()

    # ── Posts programados persistentes (cada minuto) ──────────────────────────

    @tasks.loop(minutes=1)
    async def verificar_programados():
        ahora       = datetime.now()
        programados = cargar_programados()
        for p in programados:
            try:
                publish_at = datetime.fromisoformat(p["publish_at"])
            except (KeyError, ValueError):
                eliminar_programado(p.get("id"))
                continue
            if ahora >= publish_at:
                channel = bot.get_channel(p["channel_id"])
                if channel:
                    await channel.send("Publicando post programado...")
                    await publicar_en_linkedin(p["contenido"], channel, p.get("user_id"))
                eliminar_programado(p["id"])

    @verificar_programados.before_loop
    async def before_verificar_programados():
        await bot.wait_until_ready()

    recordatorio.start()
    verificar_programados.start()
