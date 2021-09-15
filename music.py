import asyncio
import os
import discord
from discord.ext import commands
from youtube import Youtube
from help import Help
import time

Queues = {}


def time_format(seconds):
    if seconds is not None:
        seconds = int(seconds)
        h = seconds // 3600 % 24
        m = seconds % 3600 // 60
        s = seconds % 3600 % 60
        if h > 0:
            return '{:02d}:{:02d}:{:02d}'.format(h, m, s)
        else:
            return '{:02d}:{:02d}'.format(m, s)
    return None


class Entry():
    def __init__(self, applicant, filename, entryType):
        self.applicant = applicant
        self.filename = filename
        self.entryType = entryType

    def buildMetadataYoutube(self, data):
        self.title = data['track'] if 'track' in data else data['title']
        self.artist = data['artist'] if 'artist' in data else data['channel']
        self.album = data['album'] if 'album' in data else None
        self.duration = data['duration']
        self.thumbnail = data['thumbnail']
        self.url = 'https://youtu.be/' + data['id']


class Queue():
    def __init__(self, voice_client, text_channel):
        self.content = []
        self.size = 0
        self.cursor = 0
        self.starttime = 0
        self.voice_client = voice_client
        self.text_channel = text_channel

    async def startPlayback(self):
        # player = await YTDLSource.from_url(self.content[self.cursor].url, loop=self.bot.loop)
        player = discord.FFmpegPCMAudio(
            self.content[self.cursor].filename, options="-vn")
        self.voice_client.play(player, after=lambda e: self.nextSong())
        self.starttime = time.time()

        await self.text_channel.send('En lecture : %s - %s' % (self.content[self.cursor].title, self.content[self.cursor].artist))

    async def addEntry(self, song):
        self.content.append(song)
        self.size = self.size + 1
        await self.text_channel.send("%s - %s a été ajouté à la file d\'attente" % (song.title, song.artist))
        if self.size == self.cursor + 1:
            await self.startPlayback()

    def nextSong(self):
        self.cursor = self.cursor + 1
        print("next")
        if self.cursor < self.size:
            coro = self.startPlayback()
            fut = asyncio.run_coroutine_threadsafe(
                coro, self.voice_client.loop)
            try:
                fut.result()
            except:
                pass

    def removeEntry(self, index):
        self.content.pop(index)
        self.size = self.size - 1

    def moveEntry(self, frm, to):
        song = self.content[frm]
        self.content.pop(frm)
        self.content.insert(to, song)

    def getIndex(self, song):
        return self.content.index(song)

    def getSong(self, index):
        return self.content[index]


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['p', 'lire', 'jouer'])
    async def play(self, context, *, query: str = None):
        if query is None:
            return await context.send(embed=Help.get(context, 'play'))

        authorVoice = context.author.voice
        voiceClient = context.voice_client
        if authorVoice is None:
            return await context.send('Non connecté à un salon vocal')
        elif voiceClient is not None:
            await voiceClient.move_to(authorVoice.channel)
        else:
            await authorVoice.channel.connect()

        async with context.typing():
            guild = context.guild
            if guild not in Queues:
                Queues[guild] = Queue(context.voice_client, context.channel)
            queue = Queues[guild]

            if query.startswith("http") and not query.startswith(("https://youtu.be", "https://www.youtube.com", "https://youtube.com")):
                # Other streams
                pass
            else:
                # YouTube
                url = query
                if not query.startswith("https://"):
                    try:
                        result = await Youtube.searchVideos(query)
                    except:
                        return await context.send('Aucune musique trouvé')
                    url = result["link"]
                    print(url)

                try:
                    data, filename = await Youtube.downloadSong(url)
                except:
                    return await context.send('Le lien n\'est pas valide')

                applicant = context.author
                entryType = "Vidéo"
                if filename.startswith("https://"):
                    entryType = "Direct"
                elif 'Music' in data['categories']:
                    entryType = "Musique"

                entry = Entry(applicant, filename, entryType)
                entry.buildMetadataYoutube(data)

                await queue.addEntry(entry)

        return 0

    @commands.command(aliases=['np', 'en lecture'])
    async def nowplaying(self, context):
        guild = context.guild
        if guild not in Queues:
            return await context.send('Rien en lecture')

        title = Queues[guild].content[Queues[guild].cursor].title
        artist = Queues[guild].content[Queues[guild].cursor].artist
        album = Queues[guild].content[Queues[guild].cursor].album
        url = Queues[guild].content[Queues[guild].cursor].url
        entryType = Queues[guild].content[Queues[guild].cursor].entryType
        image = Queues[guild].content[Queues[guild].cursor].thumbnail
        applicant = Queues[guild].content[Queues[guild].cursor].applicant

        current = time_format(int(time.time() - Queues[guild].starttime))
        duration = time_format(
            Queues[guild].content[Queues[guild].cursor].duration)

        content = "Progression : %s / %s\n" % (current, duration)
        if album is not None:
            content += "Album : %s\n" % (album)
        content += "Type : %s" % (entryType)

        embed = discord.Embed(
            title='%s - %s' % (title, artist),
            url=url,
            description=content,
            color=0x565493
        )
        embed.set_author(name="En cours de lecture",
                         icon_url="https://i.imgur.com/C66eNWB.jpg")
        embed.set_image(url=image)
        # embed.set_thumbnail(url="https://i.imgur.com/C66eNWB.jpg")
        embed.set_footer(text="Demandé par %s" %
                         applicant.display_name, icon_url=applicant.avatar_url_as())

        return await context.send(embed=embed)

    @commands.command(aliases=['q', 'file'])
    async def queue(self, context):
        guild = context.guild
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')

        list = ""
        for i in range(Queues[guild].size):
            list = list + str(i) + " - " + Queues[guild].content[i].title + \
                " - " + Queues[guild].content[i].artist + "\n"

        return await context.send(list)

    @commands.command(aliases=['mv', 'déplacer'])
    async def move(self, context, frm: int = None, to: int = None):
        guild = context.guild
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')

        if frm is None or to is None:
            return await context.send(embed=Help.get(context, 'move'))

        if frm == to:
            return await context.send('La destination ne peut pas être égale à la source')

        if frm < Queues[guild] and frm >= 0 and to < Queues[guild] and to >= 0:
            title = Queues[guild].getSong(frm).title
            rep = Queues[guild].moveEntry(frm, to)
            if rep == 0:
                return await context.send('%s a été déplacé de %d vers %d' % (title, frm, to))
            else:
                return await context.send('Erreur lors du déplacement de la chanson')
        else:
            return await context.send('Une des deux positions est invalide')

    @commands.command(aliases=['rm', 'supprimer', 'enlever'])
    async def remove(self, context, index: int = None):
        guild = context.guild
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')

        if index is None:
            return await context.send(embed=Help.get(context, 'remove'))

        if index < Queues[guild].size and index >= 0:
            title = Queues[guild].getSong(index).title
            filename = Queues[guild].getSong(index).filename
            rep = Queues[guild].removeEntry(index)
            if rep == 0:
                os.remove(filename)
                return await context.send('%s a bien été supprimé' % (title))
            else:
                return await context.send('Erreur lors de la suppression de la chanson')
        else:
            return await context.send('L\'index %d n\'existe pas' % (index))

    @commands.command(aliases=['s', 'passer'])
    async def skip(self, context):
        voiceClient = context.voice_client
        if voiceClient is not None:
            voiceClient.stop()
        else:
            return await context.send('Aucune lecture en cours')

    @commands.command(aliases=['pauser', 'suspendre', 'uspendre', 'halte'])
    async def pause(self, context):
        voiceClient = context.voice_client
        if voiceClient is not None:
            voiceClient.pause()
            return await context.send('Mis en pause')
        else:
            return await context.send('Aucune lecture en cours')

    @commands.command(aliases=['reprendre'])
    async def resume(self, context):
        voiceClient = context.voice_client
        if voiceClient is not None:
            voiceClient.resume()
            return await context.send('Reprise de la lecture')
        else:
            return await context.send('Aucune lecture en cours')

    @commands.command(aliases=['arreter', 'stopper', 'quitter', 'leave', 'hutup'])
    async def stop(self, context):
        voiceClient = context.voice_client
        guild = context.guild
        if voiceClient is not None:
            for song in Queues[guild].content:
                if song.entryType != "live":
                    os.remove(song.filename)
            Queues.pop(guild)
            voiceClient.stop()
            await voiceClient.disconnect()
            return await context.send('Arrêté')
        else:
            return await context.send('Aucune lecture en cours')

    @commands.command()
    async def ah(self, context, *, query: str = None):
        if query == "quel plaisir":
            return await context.send('$ahh')
