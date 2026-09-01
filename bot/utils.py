import re
from datetime import datetime, timedelta

from bs4 import BeautifulSoup


def calcular_racha_actual(fechas):
    if not fechas:
        return 0
    hoy  = datetime.now().strftime("%Y-%m-%d")
    ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if fechas[-1] not in (hoy, ayer):
        return 0
    racha = 1
    for i in range(len(fechas) - 1, 0, -1):
        curr = datetime.strptime(fechas[i],     "%Y-%m-%d")
        prev = datetime.strptime(fechas[i - 1], "%Y-%m-%d")
        if (curr - prev).days == 1:
            racha += 1
        else:
            break
    return racha

def es_url(texto):
    return texto.startswith(("http://", "https://"))

def limpiar_html(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "noscript"]):
        tag.decompose()
    texto = soup.get_text(separator=" ", strip=True)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def parse_fecha_hora(texto: str) -> datetime:

    texto = texto.strip()
    ahora = datetime.now()

    for fmt in ("%H:%M", "%d/%m %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M"):
        try:
            t = datetime.strptime(texto, fmt)
            if fmt == "%H:%M":
                target = ahora.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
                if target <= ahora:
                    target += timedelta(days=1)
            elif fmt == "%d/%m %H:%M":
                target = t.replace(year=ahora.year, second=0, microsecond=0)
                if target <= ahora:
                    target = target.replace(year=ahora.year + 1)
            else:
                target = t.replace(second=0, microsecond=0)
            return target
        except ValueError:
            continue

    raise ValueError(
        "Formato no reconocido. Usa: `HH:MM`, `DD/MM HH:MM` o `DD/MM/YYYY HH:MM`"
    )
