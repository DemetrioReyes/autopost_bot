import asyncio

import requests

from .config import LINKEDIN_MEMBER_ID, LINKEDIN_TOKEN
from .storage import guardar_post

LINKEDIN_API = "https://api.linkedin.com/rest"
HEADERS_BASE = {
    "Authorization": f"Bearer {LINKEDIN_TOKEN}",
    "LinkedIn-Version": "202503",
    "X-Restli-Protocol-Version": "2.0.0",
}


async def _subir_imagen(imagen_bytes: bytes, content_type: str) -> tuple[str | None, str | None]:
    """Sube una imagen a LinkedIn. Devuelve (image_urn, error_msg)."""
    headers_json = {**HEADERS_BASE, "Content-Type": "application/json"}
    init_data = {"initializeUploadRequest": {"owner": f"urn:li:person:{LINKEDIN_MEMBER_ID}"}}

    loop = asyncio.get_event_loop()

    r_init = await loop.run_in_executor(
        None,
        lambda: requests.post(f"{LINKEDIN_API}/images?action=initializeUpload", headers=headers_json, json=init_data),
    )
    if r_init.status_code != 200:
        return None, f"Error iniciando upload de imagen: `{r_init.status_code}`"

    data       = r_init.json()
    upload_url = data["value"]["uploadUrl"]
    image_urn  = data["value"]["image"]

    upload_headers = {"Authorization": f"Bearer {LINKEDIN_TOKEN}", "Content-Type": content_type}
    r_upload = await loop.run_in_executor(
        None,
        lambda: requests.put(upload_url, headers=upload_headers, data=imagen_bytes),
    )
    if r_upload.status_code not in (200, 201):
        return None, f"Error subiendo imagen: `{r_upload.status_code}`"

    return image_urn, None


async def publicar_en_linkedin(
    contenido: str,
    channel,
    user_id: int | None = None,
    imagen_bytes: bytes | None = None,
    imagen_content_type: str = "image/jpeg",
):
    headers = {**HEADERS_BASE, "Content-Type": "application/json"}

    post_data = {
        "author": f"urn:li:person:{LINKEDIN_MEMBER_ID}",
        "commentary": contenido,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    # Subir imagen si viene adjunta
    if imagen_bytes:
        image_urn, error = await _subir_imagen(imagen_bytes, imagen_content_type)
        if error:
            await channel.send(f"No se pudo subir la imagen: {error}\nPublicando sin imagen...")
        else:
            post_data["content"] = {"media": {"id": image_urn}}

    try:
        loop = asyncio.get_event_loop()
        r = await loop.run_in_executor(
            None,
            lambda: requests.post(f"{LINKEDIN_API}/posts", headers=headers, json=post_data),
        )
        if r.status_code == 201:
            post_id = r.headers.get("x-restli-id", "desconocido")
            guardar_post(contenido, post_id, user_id)
            await channel.send(f"Publicado en LinkedIn!\nID: `{post_id}`")
        elif r.status_code == 401:
            await channel.send(
                "**Token de LinkedIn vencido o invalido.**\n"
                "Renueva el token en el Developer Portal de LinkedIn y "
                "actualiza la variable `LINKEDIN_TOKEN` en `.env`."
            )
        else:
            await channel.send(
                f"Error al publicar.\nCodigo: `{r.status_code}`\n```\n{r.text[:300]}\n```"
            )
    except Exception as e:
        await channel.send(f"Error inesperado: `{e!s}`")
