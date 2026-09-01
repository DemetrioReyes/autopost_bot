import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DISCORD_TOKEN          = os.getenv("DISCORD_TOKEN")
DISCORD_APPLICATION_ID = int(os.getenv("DISCORD_APPLICATION_ID"))
OPENAI_KEY             = os.getenv("OPENAI_KEY")
LINKEDIN_TOKEN         = os.getenv("LINKEDIN_TOKEN")
LINKEDIN_MEMBER_ID     = os.getenv("LINKEDIN_MEMBER_ID")

POSTS_FILE        = "posts_publicados.json"
DRAFTS_FILE       = "borradores.json"
CHANNELS_FILE     = "discord_channels.json"
SCHEDULED_FILE    = "scheduled_posts.json"
RECORDATORIO_DIAS = 3

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    application_id=DISCORD_APPLICATION_ID,
)

openai_client = OpenAI(api_key=OPENAI_KEY)

waiting_for_input: set[int] = set()
