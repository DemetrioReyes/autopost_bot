import hashlib
import json
import os
from datetime import datetime

from .config import CHANNELS_FILE, DRAFTS_FILE, POSTS_FILE, SCHEDULED_FILE

# ===================== POSTS =====================

def cargar_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_post(contenido, post_id, user_id=None):
    posts = cargar_posts()
    posts.append({
        "linkedin_post_id": post_id,
        "hash": hashlib.md5(contenido.encode()).hexdigest(),
        "fecha": datetime.now().isoformat(),
        "preview": contenido[:120],
        "user_id": user_id,
    })
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

def ya_publicado(contenido):
    h = hashlib.md5(contenido.encode()).hexdigest()
    return any(p["hash"] == h for p in cargar_posts())


# ===================== BORRADORES =====================

def cargar_borradores():
    if os.path.exists(DRAFTS_FILE):
        with open(DRAFTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_borrador(user_id, contenido):
    borradores = cargar_borradores()
    draft_id = int(datetime.now().timestamp())
    borradores.append({
        "id": draft_id,
        "user_id": user_id,
        "contenido": contenido,
        "fecha": datetime.now().isoformat(),
    })
    with open(DRAFTS_FILE, "w", encoding="utf-8") as f:
        json.dump(borradores, f, indent=2, ensure_ascii=False)

def eliminar_borrador(draft_id):
    borradores = [b for b in cargar_borradores() if b.get("id") != draft_id]
    with open(DRAFTS_FILE, "w", encoding="utf-8") as f:
        json.dump(borradores, f, indent=2, ensure_ascii=False)

def actualizar_borrador(draft_id, nuevo_contenido):
    borradores = cargar_borradores()
    for b in borradores:
        if b.get("id") == draft_id:
            b["contenido"] = nuevo_contenido
            break
    with open(DRAFTS_FILE, "w", encoding="utf-8") as f:
        json.dump(borradores, f, indent=2, ensure_ascii=False)


# ===================== CHANNELS =====================

def cargar_channels():
    if os.path.exists(CHANNELS_FILE):
        with open(CHANNELS_FILE) as f:
            return json.load(f)
    return []

def guardar_channel(channel_id):
    channels = cargar_channels()
    if channel_id not in channels:
        channels.append(channel_id)
        with open(CHANNELS_FILE, "w") as f:
            json.dump(channels, f)


# ===================== PROGRAMADOS =====================

def cargar_programados():
    if os.path.exists(SCHEDULED_FILE):
        with open(SCHEDULED_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_programado(prog_id, user_id, channel_id, contenido, publish_at: datetime):
    programados = cargar_programados()
    programados.append({
        "id": prog_id,
        "user_id": user_id,
        "channel_id": channel_id,
        "contenido": contenido,
        "publish_at": publish_at.isoformat(),
        "created_at": datetime.now().isoformat(),
    })
    with open(SCHEDULED_FILE, "w", encoding="utf-8") as f:
        json.dump(programados, f, indent=2, ensure_ascii=False)

def eliminar_programado(prog_id):
    programados = [p for p in cargar_programados() if p.get("id") != prog_id]
    with open(SCHEDULED_FILE, "w", encoding="utf-8") as f:
        json.dump(programados, f, indent=2, ensure_ascii=False)
