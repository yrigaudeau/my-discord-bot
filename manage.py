import discord
from discord.ext import commands
from config import Config

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
