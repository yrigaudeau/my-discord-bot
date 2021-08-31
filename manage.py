import discord
from discord.ext import commands
from discord.utils import get

class Manage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def set_prefix(self, ctx, *, channel: discord.VoiceChannel):
        """Joins a voice channel"""

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        await channel.connect()