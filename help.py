import discord
from discord.ext import commands

import json
with open("config.json") as f:
    config = json.load(f)
    f.close()

commands_desc = {
    'play': 'Permet de lire un son insane depuis Youtube ou un lien direct',
    'nowplaying': 'Permet de connaître le son en lecture et son avancement',
    'queue': 'Affiche la liste d\'attente',
    'move': 'Permet de déplacer une musique dans la liste d\'attente',
    'skip': 'Passe la musique actuelle',
    'remove': 'Supprime une musique de la liste d\'attente',
    'pause': 'Met en pause la lecture',
    'resume': 'Reprend la lecture',
    'stop': 'Arrete la lecture et vide la liste d\'attente'
}

commands_usage = {
    'play': '"lien Youtube / lien http / recherche Youtube"',
    'move': '"position actuelle" "nouvelle position"',
    'remove': '"position"',
}

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get(context, command):
        title = "Commande %s%s" % (config['prefix'], command)

        embed = discord.Embed(
            title=title,
            description=commands_desc[command],
            color=0x565493
        )
        embed.set_author(name="Aide", icon_url="https://i.imgur.com/C66eNWB.jpg")

        if command in commands_usage:
            embed.add_field(name="Utilisation", value="%s%s %s" % (config['prefix'], command, commands_usage[command]), inline=False)

        return embed

    @commands.command(aliases=['aide', 'h'])
    async def help(self, context):
        embed = discord.Embed(
            title='La page d\'aide wallah',
            description='tavu',
            color=0x565493
        )
        embed.set_author(name="Aide", icon_url="https://i.imgur.com/C66eNWB.jpg")

        for command in commands_desc:
            if command in commands_usage:
                embed.add_field(name=config['prefix']+command, value=commands_desc[command], inline=True)
                embed.add_field(name="Utilisation", value="%s%s %s" % (config['prefix'], command, commands_usage[command]), inline=True)
            else:
                embed.add_field(name=config['prefix']+command, value=commands_desc[command], inline=False)

        return await context.send(embed=embed)