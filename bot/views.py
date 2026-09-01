import asyncio
from datetime import datetime

import discord

from .ai import generar_post
from .config import bot, waiting_for_input
from .linkedin import publicar_en_linkedin
from .storage import (
    actualizar_borrador,
    eliminar_borrador,
    eliminar_programado,
    guardar_borrador,
    guardar_programado,
    ya_publicado,
)
from .utils import parse_fecha_hora

LINKEDIN_LIMIT      = 3000
LINKEDIN_WARN_LIMIT = 2800


def _boton(label, style, callback, row=None):
    boton = discord.ui.Button(label=label, style=style, row=row)
    boton.callback = callback
    return boton


async def _validar_dueno(interaction: discord.Interaction, user_id: int) -> bool:
    if interaction.user.id != user_id:
        await interaction.response.send_message("Este botón no es para ti.", ephemeral=True)
        return False
    return True


def _esperar_mensaje(user_id, channel):
    def check(m):
        return m.author.id == user_id and m.channel == channel
    return check


# ===================== TONO VIEW =====================

def crear_tono_view(user_id: int, idea: str, url: str | None = None,
                     imagen_bytes: bytes | None = None, imagen_content_type: str = "image/jpeg"):
    view = discord.ui.View(timeout=300)

    async def seleccionar_tono(interaction, tono, tono_custom=None):
        if not await _validar_dueno(interaction, user_id):
            return
        await interaction.response.edit_message(content="Generando post...", view=None)
        loop  = asyncio.get_event_loop()
        texto = await loop.run_in_executor(None, lambda: generar_post(idea, tono, tono_custom))
        if url:
            texto = f"{texto}\n\n{url}"
        chars     = len(texto)
        post_view = crear_post_view(
            user_id, idea, tono, texto,
            tono_custom=tono_custom, url=url,
            imagen_bytes=imagen_bytes, imagen_content_type=imagen_content_type,
        )
        await interaction.channel.send(f"**Propuesta:** `({chars} chars)`\n\n{texto}", view=post_view)

    def boton_de_tono(label, tono, row):
        async def callback(interaction):
            await seleccionar_tono(interaction, tono)
        return _boton(label, discord.ButtonStyle.secondary, callback, row=row)

    async def personalizado_callback(interaction):
        if not await _validar_dueno(interaction, user_id):
            return
        # Usamos send_message para pedir instrucciones — la interacción queda respondida aquí.
        # NO llamamos a seleccionar_tono después porque ese flujo intenta hacer
        # edit_message sobre la misma interacción ya respondida, lo que falla silenciosamente.
        await interaction.response.send_message(
            "Describe el tono o instrucciones para el post "
            "(ej: `más técnico, con métricas reales, tono directo sin metáforas`):"
        )
        waiting_for_input.add(user_id)
        check = _esperar_mensaje(user_id, interaction.channel)
        try:
            msg         = await bot.wait_for("message", check=check, timeout=120)
            tono_custom = msg.content.strip()
            await interaction.channel.send("Generando post con tono personalizado...")
            loop  = asyncio.get_event_loop()
            texto = await loop.run_in_executor(None, lambda: generar_post(idea, "custom", tono_custom))
            if url:
                texto = f"{texto}\n\n{url}"
            chars     = len(texto)
            post_view = crear_post_view(
                user_id, idea, "custom", texto,
                tono_custom=tono_custom, url=url,
                imagen_bytes=imagen_bytes, imagen_content_type=imagen_content_type,
            )
            await interaction.channel.send(f"**Propuesta:** `({chars} chars)`\n\n{texto}", view=post_view)
        except asyncio.TimeoutError:
            await interaction.channel.send("Tiempo agotado. Elige un tono de nuevo.")
        finally:
            waiting_for_input.discard(user_id)

    view.add_item(boton_de_tono("Técnico", "tecnico", row=0))
    view.add_item(boton_de_tono("Historia personal", "historia", row=0))
    view.add_item(boton_de_tono("Opinión directa", "opinion", row=1))
    view.add_item(boton_de_tono("Tip rápido", "tip", row=1))
    view.add_item(boton_de_tono("Descubrimiento", "descubrimiento", row=2))
    view.add_item(_boton("Personalizado", discord.ButtonStyle.primary, personalizado_callback, row=2))
    return view


# ===================== POST VIEW =====================

def crear_post_view(user_id: int, idea: str, tono: str, texto: str,
                     tono_custom: str | None = None, url: str | None = None,
                     imagen_bytes: bytes | None = None, imagen_content_type: str = "image/jpeg"):
    view = discord.ui.View(timeout=600)

    async def publicar_callback(interaction):
        if not await _validar_dueno(interaction, user_id):
            return
        if ya_publicado(texto):
            await interaction.response.send_message("Este post ya fue publicado anteriormente.", ephemeral=True)
            return
        chars = len(texto)
        if chars > LINKEDIN_LIMIT:
            await interaction.response.send_message(
                f"El post tiene **{chars} caracteres** y supera el límite de LinkedIn ({LINKEDIN_LIMIT}). "
                "Edítalo antes de publicar.",
                ephemeral=True,
            )
            return
        # Primero editamos el mensaje para quitar los botones, luego mandamos el aviso como followup
        await interaction.response.edit_message(view=None)
        if chars > LINKEDIN_WARN_LIMIT:
            await interaction.followup.send(
                f"Aviso: el post tiene **{chars}/{LINKEDIN_LIMIT} caracteres**. Publicando...",
                ephemeral=True,
            )
        await publicar_en_linkedin(texto, interaction.channel, interaction.user.id, imagen_bytes, imagen_content_type)

    async def regenerar_callback(interaction):
        if not await _validar_dueno(interaction, user_id):
            return
        await interaction.response.edit_message(content="Regenerando...", view=None)
        loop        = asyncio.get_event_loop()
        nuevo_texto = await loop.run_in_executor(None, lambda: generar_post(idea, tono, tono_custom))
        if url:
            nuevo_texto = f"{nuevo_texto}\n\n{url}"
        chars     = len(nuevo_texto)
        post_view = crear_post_view(
            user_id, idea, tono, nuevo_texto,
            tono_custom=tono_custom, url=url,
            imagen_bytes=imagen_bytes, imagen_content_type=imagen_content_type,
        )
        await interaction.channel.send(f"**Nueva propuesta:** `({chars} chars)`\n\n{nuevo_texto}", view=post_view)

    async def programar_callback(interaction):
        if not await _validar_dueno(interaction, user_id):
            return
        if imagen_bytes:
            await interaction.response.send_message(
                "Los posts programados no soportan imagen adjunta. Publica directamente o guarda el borrador.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "A qué fecha y hora publicar?\n"
            "Formatos aceptados: `HH:MM` | `DD/MM HH:MM` | `DD/MM/YYYY HH:MM`"
        )
        waiting_for_input.add(user_id)
        check = _esperar_mensaje(user_id, interaction.channel)
        try:
            msg    = await bot.wait_for("message", check=check, timeout=120)
            target = parse_fecha_hora(msg.content)

            prog_id = int(datetime.now().timestamp())
            guardar_programado(prog_id, user_id, interaction.channel.id, texto, target)

            fecha_str = target.strftime("%d/%m/%Y a las %H:%M")
            delay     = (target - datetime.now()).total_seconds()
            horas_r   = int(delay // 3600)
            mins_r    = int((delay % 3600) // 60)
            await interaction.channel.send(
                f"Post programado para el **{fecha_str}** (en {horas_r}h {mins_r}m)\n"
                "Usa `/programados` para verlo o cancelarlo."
            )
        except ValueError as e:
            await interaction.channel.send(str(e))
        except asyncio.TimeoutError:
            await interaction.channel.send("Tiempo agotado.")
        finally:
            waiting_for_input.discard(user_id)

    async def editar_callback(interaction):
        if not await _validar_dueno(interaction, user_id):
            return
        await interaction.response.send_message("Envía tu versión editada del post:")
        waiting_for_input.add(user_id)
        check = _esperar_mensaje(user_id, interaction.channel)
        try:
            msg          = await bot.wait_for("message", check=check, timeout=300)
            nuevo_texto  = msg.content
            chars        = len(nuevo_texto)
            post_view    = crear_post_view(
                user_id, idea, tono, nuevo_texto,
                tono_custom=tono_custom, url=url,
                imagen_bytes=imagen_bytes, imagen_content_type=imagen_content_type,
            )
            await interaction.channel.send(f"**Post editado:** `({chars} chars)`\n\n{nuevo_texto}", view=post_view)
        except asyncio.TimeoutError:
            await interaction.channel.send("Tiempo agotado. Usa el botón Editar de nuevo.")
        finally:
            waiting_for_input.discard(user_id)

    async def borrador_callback(interaction):
        if not await _validar_dueno(interaction, user_id):
            return
        guardar_borrador(user_id, texto)
        nota = " (sin imagen adjunta)" if imagen_bytes else ""
        await interaction.response.send_message(
            f"Borrador guardado{nota}. Usa `/borradores` para verlo.", ephemeral=True
        )

    async def descartar_callback(interaction):
        if not await _validar_dueno(interaction, user_id):
            return
        await interaction.response.edit_message(content="Post descartado.", view=None)

    view.add_item(_boton("Publicar", discord.ButtonStyle.success, publicar_callback, row=0))
    view.add_item(_boton("Regenerar", discord.ButtonStyle.primary, regenerar_callback, row=0))
    view.add_item(_boton("Programar", discord.ButtonStyle.secondary, programar_callback, row=0))
    view.add_item(_boton("Editar", discord.ButtonStyle.secondary, editar_callback, row=1))
    view.add_item(_boton("Guardar borrador", discord.ButtonStyle.secondary, borrador_callback, row=1))
    view.add_item(_boton("Descartar", discord.ButtonStyle.danger, descartar_callback, row=1))
    return view


# ===================== DRAFT VIEW =====================

def crear_draft_view(user_id: int, draft_id: int, contenido: str):
    view = discord.ui.View(timeout=600)

    async def publicar_callback(interaction):
        if not await _validar_dueno(interaction, user_id):
            return
        chars = len(contenido)
        if chars > LINKEDIN_LIMIT:
            await interaction.response.send_message(
                f"El borrador tiene **{chars} caracteres** y supera el límite de LinkedIn ({LINKEDIN_LIMIT}). "
                "Edítalo antes de publicar.",
                ephemeral=True,
            )
            return
        await interaction.response.edit_message(view=None)
        await publicar_en_linkedin(contenido, interaction.channel, interaction.user.id)
        eliminar_borrador(draft_id)

    async def editar_callback(interaction):
        if not await _validar_dueno(interaction, user_id):
            return
        await interaction.response.send_message("Envía el contenido actualizado del borrador:")
        waiting_for_input.add(user_id)
        check = _esperar_mensaje(user_id, interaction.channel)
        try:
            msg             = await bot.wait_for("message", check=check, timeout=300)
            nuevo_contenido = msg.content
            actualizar_borrador(draft_id, nuevo_contenido)
            chars = len(nuevo_contenido)
            await interaction.channel.send(f"Borrador actualizado (`{chars} chars`). Usa `/borradores` para verlo.")
        except asyncio.TimeoutError:
            await interaction.channel.send("Tiempo agotado.")
        finally:
            waiting_for_input.discard(user_id)

    async def eliminar_callback(interaction):
        if not await _validar_dueno(interaction, user_id):
            return
        eliminar_borrador(draft_id)
        await interaction.response.edit_message(content="Borrador eliminado.", view=None)

    view.add_item(_boton("Publicar", discord.ButtonStyle.success, publicar_callback))
    view.add_item(_boton("Editar", discord.ButtonStyle.secondary, editar_callback))
    view.add_item(_boton("Eliminar", discord.ButtonStyle.danger, eliminar_callback))
    return view


# ===================== SCHEDULED VIEW =====================

def crear_scheduled_view(user_id: int, prog_id: int):
    view = discord.ui.View(timeout=300)

    async def cancelar_callback(interaction):
        if not await _validar_dueno(interaction, user_id):
            return
        eliminar_programado(prog_id)
        await interaction.response.edit_message(content="Post programado cancelado.", view=None)

    view.add_item(_boton("Cancelar programación", discord.ButtonStyle.danger, cancelar_callback))
    return view
