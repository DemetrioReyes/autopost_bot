import asyncio
from datetime import datetime

import discord

from .ai import generar_ideas
from .storage import cargar_borradores, cargar_posts, cargar_programados, guardar_channel
from .utils import calcular_racha_actual
from .views import crear_draft_view, crear_scheduled_view


def registrar_comandos(bot):
    @bot.tree.command(name="start", description="Inicia el bot y muestra los comandos disponibles")
    async def start(interaction: discord.Interaction):
        guardar_channel(interaction.channel_id)
        await interaction.response.send_message(
            "Bot listo.\n\n"
            "**Comandos:**\n"
            "`/ideas` — sugerencias de temas\n"
            "`/stats` — tus estadísticas de publicación\n"
            "`/historial` — últimos posts publicados\n"
            "`/borradores` — borradores guardados\n"
            "`/programados` — posts en cola de publicación\n\n"
            "**Uso:**\n"
            "`!post tu idea aquí` — genera un post\n"
            "`!post https://url.com` — genera post desde un artículo\n"
            "`!post tu idea` + imagen adjunta — genera y publica con imagen en LinkedIn"
        )

    @bot.tree.command(name="ideas", description="Genera 5 ideas de posts para LinkedIn")
    async def ideas_cmd(interaction: discord.Interaction):
        await interaction.response.defer()
        loop  = asyncio.get_event_loop()
        texto = await loop.run_in_executor(None, generar_ideas)
        await interaction.followup.send(texto)

    @bot.tree.command(name="stats", description="Ver tus estadísticas de publicación en LinkedIn")
    async def stats_cmd(interaction: discord.Interaction):
        user_id = interaction.user.id
        todos   = cargar_posts()
        posts   = [p for p in todos if p.get("user_id") == user_id or p.get("user_id") is None]

        if not posts:
            await interaction.response.send_message("No hay posts publicados aún.")
            return

        ahora             = datetime.now()
        mes_actual        = ahora.strftime("%Y-%m")
        posts_mes         = sum(1 for p in posts if p["fecha"].startswith(mes_actual))
        ultimo            = datetime.fromisoformat(posts[-1]["fecha"])
        dias_desde_ultimo = (ahora - ultimo).days
        fechas_unicas     = sorted({p["fecha"][:10] for p in posts})
        racha             = calcular_racha_actual(fechas_unicas)
        total             = len(posts)
        programados_count = sum(1 for p in cargar_programados() if p.get("user_id") == user_id)

        await interaction.response.send_message(
            f"**Tus estadísticas de LinkedIn:**\n\n"
            f"Posts este mes: **{posts_mes}**\n"
            f"Total publicados: **{total}**\n"
            f"Último post: hace **{dias_desde_ultimo}** días\n"
            f"Racha actual: **{racha}** día(s) consecutivo(s)\n"
            f"Posts en cola: **{programados_count}**"
        )

    @bot.tree.command(name="historial", description="Ver los últimos posts publicados en LinkedIn")
    async def historial_cmd(interaction: discord.Interaction):
        user_id = interaction.user.id
        todos   = cargar_posts()
        posts   = [p for p in todos if p.get("user_id") == user_id or p.get("user_id") is None]

        if not posts:
            await interaction.response.send_message("No hay posts publicados aún.")
            return

        texto = "**Últimos posts publicados:**\n\n"
        for p in posts[-5:][::-1]:
            fecha   = p["fecha"][:10]
            preview = p["preview"][:80].replace("**", "").replace("`", "")
            texto  += f"`{fecha}` — {preview}...\n\n"
        await interaction.response.send_message(texto)

    @bot.tree.command(name="borradores", description="Ver y gestionar borradores guardados")
    async def borradores_cmd(interaction: discord.Interaction):
        user_id        = interaction.user.id
        mis_borradores = [b for b in cargar_borradores() if b.get("user_id") == user_id]
        if not mis_borradores:
            await interaction.response.send_message("No tienes borradores guardados.")
            return
        await interaction.response.send_message(f"Tienes **{len(mis_borradores)}** borrador(es):")
        for b in mis_borradores:
            fecha   = b["fecha"][:10]
            preview = b["contenido"][:300].replace("**", "").replace("`", "")
            chars   = len(b["contenido"])
            view    = crear_draft_view(user_id, b["id"], b["contenido"])
            await interaction.channel.send(
                f"**Borrador — {fecha}** `({chars} chars)`\n\n{preview}...",
                view=view,
            )

    @bot.tree.command(name="programados", description="Ver y cancelar posts programados")
    async def programados_cmd(interaction: discord.Interaction):
        user_id         = interaction.user.id
        mis_programados = [p for p in cargar_programados() if p.get("user_id") == user_id]
        if not mis_programados:
            await interaction.response.send_message("No tienes posts programados.")
            return
        await interaction.response.send_message(f"Tienes **{len(mis_programados)}** post(s) en cola:")
        for p in mis_programados:
            publish_at = datetime.fromisoformat(p["publish_at"])
            fecha_str  = publish_at.strftime("%d/%m/%Y a las %H:%M")
            preview    = p["contenido"][:200].replace("**", "").replace("`", "")
            chars      = len(p["contenido"])
            view       = crear_scheduled_view(user_id, p["id"])
            await interaction.channel.send(
                f"**Programado para {fecha_str}** `({chars} chars)`\n\n{preview}...",
                view=view,
            )
