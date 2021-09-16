import os
import discord
from discord.ext import commands

from music import Music
from fun import Fun
from manage import Manage
from help import Help
from config import Config

PREFIX = Config.getPrefix()
TOKEN = Config.conf['token']

if __name__ == "__main__":
    if os.path.isdir('dj-patrick'):
        for f in os.listdir('dj-patrick'):
            os.remove('dj-patrick/' + f)
    else:
        os.mkdir('dj-patrick')

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
