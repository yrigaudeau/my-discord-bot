import os
import discord
from discord.ext import commands

from music import Music
from fun import Fun
from manage import Manage
from help import Help

import json
with open("config.json") as f:
    config = json.load(f)
    f.close()

description = 'Alors, on attend pas Patrick ???'
PREFIX = config['prefix']
TOKEN = config['token']

if __name__ == "__main__":
    if not os.path.isdir('dj-patrick'):
        os.mkdir('dj-patrick')

    bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX), description=description, help_command=None)

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
