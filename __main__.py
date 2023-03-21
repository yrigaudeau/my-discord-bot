import os
import discord
from discord.ext import commands

from config import config, DLDIR
from help import Help
from music import Music
from manage import Manage
from fun import Fun
if config.FoxDotEnabled is True:
    from foxdot import Foxdot

if __name__ == "__main__":
    if os.path.isdir(DLDIR):
        for f in os.listdir(DLDIR):
            os.remove(DLDIR + f)
    else:
        os.mkdir(DLDIR)

    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix=lambda e, f: config.getPrefix(), help_command=None, intents=intents)

    @bot.event
    async def on_ready():
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=config.getPrefix()+"help"))

        print('Logged in as {0} ({0.id})'.format(bot.user))
        print('------')

    @bot.event
    async def on_message(message):
        if message.author.id == bot.user.id or message.author.bot:
            return

        if config.FoxDotEnabled is True:
            await Foxdot.send_command(message)
        await Fun.chocolatine(message)

        await bot.process_commands(message)

    bot.add_cog(Music(bot))
    bot.add_cog(Fun(bot))
    bot.add_cog(Manage(bot))
    bot.add_cog(Help(bot))
    if config.FoxDotEnabled is True:
        bot.add_cog(Foxdot(bot))
    bot.run(config.token)
