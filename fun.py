import re
import discord
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ah(self, context, *, query: str = None):
        if query == "quel plaisir":
            return await context.send('$ahh')

    async def chocolatine(message):
        words = re.split('\s+|\'|"', message.content)
        for word in words:
            if word.endswith("tine"):
                await message.reply("Sans te contredire %s, on ne dit pas %s mais pain au %s !" % (message.author.display_name, word, word[:-3]))
