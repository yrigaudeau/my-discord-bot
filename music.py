import asyncio
import os
import discord
from discord.ext import commands
from youtube import Youtube
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


class Song():
    def __init__(self, applicant, filename):
        self.filename = filename
        self.applicant = applicant

    def buildMetadata(self, data):
        self.title = data['track'] if 'track' in data else data['title']
        self.album = data['album'] if 'album' in data else None
        self.artist = data['artist'] if 'artist' in data else data['channel']
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
        #player = await YTDLSource.from_url(self.content[self.cursor].url, loop=self.bot.loop)
        player = discord.FFmpegPCMAudio(self.content[self.cursor].filename, options="-vn")
        self.voice_client.play(player, after=lambda e: self.nextSong())
        self.starttime = time.time()

        await self.text_channel.send('En lecture : %s' % (self.content[self.cursor].title))

    async def addEntry(self, song):
        self.content.append(song)
        self.size = self.size + 1
        await self.text_channel.send("%s a été ajouté à la file d\'attente" % (song.title))
        if self.size == self.cursor + 1:
            await self.startPlayback()
        return 0

    def nextSong(self):
        self.cursor = self.cursor + 1
        print("hey")
        if self.cursor < self.size:
            coro = self.startPlayback()
            fut = asyncio.run_coroutine_threadsafe(
                coro, self.voice_client.loop)
            try:
                fut.result()
            except:
                pass

    def removeEntry(self, index):
        if index >= 0 and index < self.size:
            self.content.pop(index)
            self.size = self.size - 1
            return 0
        else:
            return None

    def moveEntry(self, frm, to):
        if frm >= 0 and frm < self.size and to >= 0 and to < self.size and to != frm:
            # si frm avant to alors insert +1
            # sinon ok
            song = self.content[frm]
            self.content.pop(frm)
            self.content.insert(to, song)
            return 0
        else:
            return None

    def getIndex(self, song):
        return self.content.index(song)

    def getSong(self, index):
        if index >= 0 and index < self.size:
            return self.content[index]
        else:
            return None


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['p', 'lire', 'jouer'])
    async def play(self, context, *, query: str = None):
        """Plays a song from YouTube"""

        if query is None:
            return await context.send('Aucune musique n\'est précisé')

        authorVoice = context.author.voice
        voiceClient = context.voice_client
        if authorVoice is None:
            return await context.send('Non connecté à un salon vocal')
        elif voiceClient is not None:
            await voiceClient.move_to(authorVoice.channel)
        else:
            await authorVoice.channel.connect()

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
            song = Song(applicant, filename)
            song.buildMetadata(data)

            await queue.addEntry(song)

        return 0

    @commands.command(aliases=['np', 'en lecture'])
    async def nowplaying(self, context):
        guild = context.guild
        if guild not in Queues:
            return await context.send('Rien en lecture')

        title = Queues[guild].content[Queues[guild].cursor].title
        current = time_format(
            int(time.time() - Queues[guild].starttime))
        duration = time_format(
            Queues[guild].content[Queues[guild].cursor].duration)
        thumbnail = Queues[guild].content[Queues[guild].cursor].thumbnail

        await context.send('En lecture : %s\nProgression : %s / %s\n%s' % (title, current, duration, thumbnail))

    @commands.command(aliases=['q', 'file'])
    async def queue(self, context):
        guild = context.guild
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')

        list = ""
        for i in range(Queues[guild].size):
            list = list + str(i) + " - " + \
                Queues[guild].content[i].title + "\n"
        return await context.send(list)

    @commands.command(aliases=['mv', 'déplacer'])
    async def move(self, context, frm: int, to: int):
        guild = context.guild
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')
        t = Queues[guild].getSong(frm).title
        r = Queues[guild].moveEntry(frm, to)
        if r == 0:
            return await context.send('%s a été déplacé de %d vers %d' % (t, frm, to))
        else:
            return await context.send('Erreur lors du déplacement de la chanson')

    @commands.command(aliases=['rm', 'supprimer', 'enlever'])
    async def remove(self, context, index: int):
        guild = context.guild
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')
        t = Queues[guild].getSong(index).title
        r = Queues[guild].removeEntry(index)
        if r == 0:
            return await context.send('%s a bien été supprimé' % (t))
        else:
            return await context.send('Erreur lors de la suppression de la chanson')

    @commands.command(aliases=['s', 'passer'])
    async def skip(self, context):
        voiceClient = context.voice_client
        if voiceClient is not None:
            voiceClient.stop()
        else:
            return await context.send('Aucune lecture en cours')

    @commands.command(aliases=['pauser'])
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

    @commands.command(aliases=['arreter', 'stopper', 'quitter', 'leave'])
    async def stop(self, context):
        voiceClient = context.voice_client
        guild = context.guild
        if voiceClient is not None:
            Queues.pop(guild)
            voiceClient.stop()
            await voiceClient.disconnect()
            return await context.send('Arrêté')
        else:
            return await context.send('Aucune lecture en cours')
