import os
import discord
from discord.ext import commands

from config import Config
from help import Help
from music import Music
from manage import Manage
from fun import Fun

PREFIX = Config.getPrefix()
TOKEN = Config.conf['token']
WORKDIR = Config.conf['workDir']

if __name__ == "__main__":
    if os.path.isdir(WORKDIR):
        for f in os.listdir(WORKDIR):
            os.remove(WORKDIR + f)
    else:
        os.mkdir(WORKDIR)

    bot = commands.Bot(command_prefix=lambda e, f: Config.getPrefix(), help_command=None)

    @bot.event
    async def on_ready():
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=PREFIX+"help"))
        print('Logged in as {0} ({0.id})'.format(bot.user))
        print('------')

    bot.add_cog(Music(bot))
    bot.add_cog(Fun(bot))
    bot.add_cog(Manage(bot))
    bot.add_cog(Help(bot))
    bot.run(TOKEN)
