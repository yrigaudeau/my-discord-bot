from discord.ext import commands
from config import Config


class Manage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='set-prefix')
    async def set_prefix(self, context, *, query: str = None):
        Config.setPrefix(query)

    