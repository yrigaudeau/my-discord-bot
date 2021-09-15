import os
import discord
from discord.ext import commands

import json
with open(os.path.dirname(os.path.realpath(__file__)) + "/config.json") as f:
    config = json.load(f)
    f.close()


class Manage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='set-prefix')
    async def set_prefix(self, context, *, query: str = None):
        pass
