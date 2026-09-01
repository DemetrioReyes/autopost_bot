from prompt_config import construir_prompt, construir_prompt_ideas

from .config import openai_client


def generar_post(idea: str, tono: str, tono_custom: str | None = None) -> str:
    r = openai_client.chat.completions.create(
        model="gpt-4",
        max_tokens=550,
        messages=[{"role": "user", "content": construir_prompt(idea, tono, tono_custom)}],
    )
    return r.choices[0].message.content

def generar_ideas() -> str:
    r = openai_client.chat.completions.create(
        model="gpt-4",
        max_tokens=500,
        messages=[{"role": "user", "content": construir_prompt_ideas()}],
    )
    return r.choices[0].message.content
