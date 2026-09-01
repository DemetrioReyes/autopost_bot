# Autopost Bot

Bot de Discord que genera y publica posts de LinkedIn con ayuda de IA (OpenAI). Desde Discord puedes pedir ideas, generar un post a partir de un texto o de un artículo (URL), elegir el tono, adjuntar una imagen, guardar borradores, programar publicaciones y ver estadísticas de tu actividad.

## Requisitos

- Python 3.10 o superior
- [uv](https://docs.astral.sh/uv/) (gestor de paquetes usado en este proyecto)
- Una aplicación de Discord con un bot creado ([Discord Developer Portal](https://discord.com/developers/applications))
- Una API key de OpenAI ([platform.openai.com](https://platform.openai.com/api-keys))
- Un token de acceso de LinkedIn con permisos para publicar (`w_member_social`) y tu Member ID de LinkedIn

## Instalación

1. Clona el repositorio:

   ```bash
   git clone git@github.com:DemetrioReyes/autopost_bot.git
   cd autopost_bot
   ```

2. Instala las dependencias con uv (crea el entorno virtual automáticamente):

   ```bash
   uv sync
   ```

3. Copia el archivo de variables de entorno de ejemplo:

   ```bash
   cp .env.example .env
   ```

4. Completa `.env` con tus credenciales (ver detalle abajo).

## Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `DISCORD_TOKEN` | Sí | Token del bot, en Discord Developer Portal → tu app → **Bot** → Reset Token |
| `DISCORD_APPLICATION_ID` | Sí | Application ID, en Discord Developer Portal → tu app → **General Information** |
| `OPENAI_KEY` | Sí | API key de OpenAI |
| `LINKEDIN_TOKEN` | Sí | Access token de LinkedIn (permiso `w_member_social`) |
| `LINKEDIN_MEMBER_ID` | Sí | Tu ID numérico de miembro de LinkedIn |
| `DISCORD_PUBLIC_KEY` | No | Reservada para verificación de interacciones vía HTTP; no usada actualmente |
| `CHALLENGE_WEBHOOK_URL` | No | Reservada para uso futuro; no usada actualmente |
| `WEB_URL` | No | Reservada para uso futuro; no usada actualmente |

### Obtener el token y datos del bot de Discord

1. Ve a [discord.com/developers/applications](https://discord.com/developers/applications) y crea una nueva aplicación.
2. En **Bot**, crea el bot, copia el token → `DISCORD_TOKEN`.
3. Activa el intent **Message Content Intent** en la misma sección (necesario para leer los mensajes `!post`).
4. En **General Information**, copia el **Application ID** → `DISCORD_APPLICATION_ID`.
5. En **OAuth2 → URL Generator**, marca los scopes `bot` y `applications.commands`, y los permisos `Send Messages`, `Read Message History`, `Attach Files`. Usa la URL generada para invitar el bot a tu servidor.

### Obtener el token de LinkedIn

1. Crea una app en el [LinkedIn Developer Portal](https://www.linkedin.com/developers/apps) y asóciala a tu perfil/página.
2. Solicita el producto **Share on LinkedIn** (o el que otorgue el scope `w_member_social`).
3. Genera un access token con ese scope siguiendo el flujo OAuth 2.0 de LinkedIn → `LINKEDIN_TOKEN`.
4. Obtén tu Member ID (por ejemplo desde la respuesta del endpoint `/v2/userinfo` con el mismo token) → `LINKEDIN_MEMBER_ID`.

   > El token de LinkedIn expira periódicamente. Si el bot responde "Token de LinkedIn vencido o inválido", regenera el token en el Developer Portal y actualiza `LINKEDIN_TOKEN` en `.env`.

## Ejecutar el bot

```bash
uv run app.py
```

Si todo está bien configurado verás en consola:

```
Bot encendido como <nombre-del-bot> y esperando ideas...
```

## Uso

Dentro del canal de Discord donde invitaste al bot:

- `/start` — muestra el mensaje de bienvenida y la lista de comandos
- `/ideas` — genera 5 ideas de posts para LinkedIn
- `/stats` — estadísticas de publicación (posts del mes, racha, etc.)
- `/historial` — últimos posts publicados
- `/borradores` — ver y gestionar borradores guardados
- `/programados` — ver y cancelar posts en cola de publicación
- `!post tu idea aquí` — genera un post a partir de un texto libre
- `!post https://url.com` — genera un post a partir del contenido de un artículo
- `!post tu idea` + imagen adjunta — genera el post y lo publica con imagen en LinkedIn

Tras `!post`, el bot pregunta el tono deseado; luego puedes revisar, editar, guardar como borrador, programar o publicar directamente en LinkedIn.

## Datos persistidos

El bot guarda estado en archivos JSON locales (ignorados por git, ya que son datos de ejecución, no configuración):

- `posts_publicados.json` — historial de posts publicados
- `discord_channels.json` — canales donde se ha usado el bot
- `borradores.json` — borradores guardados
- `scheduled_posts.json` — posts programados pendientes

## Estructura del proyecto

```
app.py              # Punto de entrada
prompt_config.py    # Prompts usados para generar contenido con IA
bot/
  config.py          # Carga de variables de entorno y cliente Discord/OpenAI
  commands.py        # Slash commands (/start, /ideas, /stats, etc.)
  events.py          # Manejo de mensajes (!post) y adjuntos
  ai.py              # Generación de ideas/posts con OpenAI
  linkedin.py        # Publicación de posts e imágenes en LinkedIn
  reminder.py         # Tareas periódicas: recordatorios y posts programados
  storage.py          # Lectura/escritura de los JSON de estado
  utils.py            # Utilidades (detección de URL, limpieza de HTML, rachas)
  views.py            # Componentes de UI de Discord (botones, selects)
```

## Desarrollo

Lint con [ruff](https://docs.astral.sh/ruff/):

```bash
uv run ruff check .
```
