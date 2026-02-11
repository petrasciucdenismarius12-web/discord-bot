import discord
from discord.ext import commands
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

TOKEN = os.getenv("MTQ3MTE4MzIxMDQzOTUxMjI1OQ.GULJKA.g2jqxyd894sBzTUl1uQpY2hL8xlcfWHodQPhbMN")

if not TOKEN:
    print("ERROR: DISCORD_TOKEN not found!")
else:
    bot.run(TOKEN)
