import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from config import getToken
from Labs import Labs

bot = commands.Bot(command_prefix="^", case_insensitive=True)

@bot.event
async def on_ready():
    # When connected, change presence and start twitch bot
    print(f"Logged in as {bot.user}")

if __name__ == "__main__":
    bot.add_cog(Labs(bot))
    bot.run(getToken())