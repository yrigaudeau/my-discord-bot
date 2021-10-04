import os
import discord
from discord.ext import commands

from config import Config, DLDIR
from help import Help
from music import Music
from manage import Manage
from fun import Fun

TOKEN = Config.token

if __name__ == "__main__":
    if os.path.isdir(DLDIR):
        for f in os.listdir(DLDIR):
            os.remove(DLDIR + f)
    else:
        os.mkdir(DLDIR)

    bot = commands.Bot(command_prefix=lambda e, f: Config.getPrefix(), help_command=None)

    @bot.event
    async def on_ready():
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=Config.getPrefix()+"help"))
        print('Logged in as {0} ({0.id})'.format(bot.user))
        print('------')

    @bot.event
    async def on_message(message):
        if message.author.id == bot.user.id or message.author.bot:
            return

        await Fun.chocolatine(message)
        await bot.process_commands(message)

    bot.add_cog(Music(bot))
    bot.add_cog(Fun(bot))
    bot.add_cog(Manage(bot))
    bot.add_cog(Help(bot))
    bot.run(TOKEN)
