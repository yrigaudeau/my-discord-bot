import os
import discord
import asyncio
from discord.ext import commands
from config import Config

WORKDIR = Config.conf['workDir']


class Manage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='set-prefix')
    @commands.has_permissions(manage_messages=True)
    async def set_prefix(self, context, *, query: str = None):
        if " " in query:
            return await context.send("Préfixe invalide")

        prefix = query
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=prefix+"help"))
        Config.setPrefix(prefix)
        return await context.send("Le Préfixe à été défini sur %s" % (prefix))

    @set_prefix.error
    async def set_prefix_error(self, context, error):
        if isinstance(error, commands.MissingPermissions):
            return await context.send("Vous n'avez pas la permission d'éxécuter cette commande !")

    @commands.command(aliases=['hutdown'])
    @commands.is_owner()
    async def shutdown(self, context):
        authorVoice = context.author.voice
        voiceClient = context.voice_client
        if authorVoice is not None:
            if voiceClient is not None:
                await voiceClient.move_to(authorVoice.channel)
            else:
                voiceClient = await authorVoice.channel.connect(timeout=600, reconnect=True)
            if voiceClient.is_playing():
                voiceClient.stop()
            player = discord.FFmpegPCMAudio("shutdown.webm", options="-vn")
            voiceClient.play(player)
            await asyncio.sleep(2)
        await voiceClient.disconnect()
        await context.send("Adios...")
        for f in os.listdir(WORKDIR):
            os.remove(WORKDIR + f)
        exit(0)

    @shutdown.error
    async def shutdown_error(self, context, error):
        if isinstance(error, commands.NotOwner):
            return await context.send("Je ne répond qu'au maître")
        else:
            print(error)
