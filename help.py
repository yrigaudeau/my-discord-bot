import discord

help_commands = {

}

help_general = discord.Embed()

class Help():
    def helpCommand(command):
        return help_commands[command]

    def help():
        return help_general