from dotenv import load_dotenv
from os import getenv
from discord.ext import commands

from music import Music
from fun import Fun
from manage import Manage

load_dotenv()

description = 'Relatively simple music bot example'
PREFIX = '$'
TOKEN = getenv("TOKEN")

if __name__ == "__main__":
    bot = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX), description=description)
    @bot.event
    async def on_ready():
        print('Logged in as {0} ({0.id})'.format(bot.user))
        print('------')

    bot.add_cog(Music(bot))
    bot.add_cog(Fun(bot))
    bot.add_cog(Manage(bot))
    bot.run(TOKEN)
