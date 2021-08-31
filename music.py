import asyncio
from discord.ext import commands, tasks
from youtube import Youtube, YTDLSource
from multiprocessing import Process
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
    def __init__(self, applicant, title, artist, duration, url, source, thumbnail=None):
        self.title = title
        self.artist = artist
        self.url = url
        self.thumbnail = thumbnail
        self.source = source
        self.applicant = applicant
        self.duration = duration


class Queue():
    def __init__(self, bot, voice_client, text_channel):
        self.content = []
        self.size = 0
        self.cursor = 0
        self.elapsedtime = 0
        self.bot = bot
        self.voice_client = voice_client
        self.text_channel = text_channel
        self.lock = asyncio.Lock()

    async def progressCount(self):
        pass

    @tasks.loop(seconds=0.1)
    async def progressLoop(self):
        async with self.lock:
            await self.progressCount()


    async def startPlayback(self):
        player = await YTDLSource.from_url(self.content[self.cursor].url, loop=self.bot.loop, stream=True)
        self.voice_client.play(player, after=lambda e: self.nextSong())
        self.progressLoop.start()

        await self.text_channel.send('En lecture : {}'.format(self.content[self.cursor].title))

    async def addEntry(self, song):
        self.content.append(song)
        self.size = self.size + 1
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
        self.content.pop(index)
        if self.size > 0:
            self.size = self.size - 1
            return 0
        else:
            return None

    def moveEntry(self, frm, to):
        song = self.content[frm]
        self.content.insert(to, song)
        self.removeEntry(frm)
        return 0

    def getIndex(self, song):
        return self.content.index(song)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['p', 'lire', 'jouer'])
    async def play(self, context, *, query: str = None):
        """Plays a song from YouTube"""

        if query is None:
            return await context.send('Aucune musique n\'est précisé')

        voiceChannel = context.author.voice.channel
        voiceClient = context.voice_client
        if voiceChannel is None:
            return await context.send('Non connecté à un salon vocal')
        elif voiceClient is not None:
            await voiceClient.move_to(voiceChannel)
        else:
            await voiceChannel.connect()

        guild = context.guild
        if guild not in Queues:
            Queues[guild] = Queue(
                self.bot, context.voice_client, context.channel)
        queue = Queues[guild]

        if query.startswith("http"):
            pass
        elif query.startswith(("https://youtu.be", "https://www.youtube.com", "https://youtube.com")):
            pass
        else:
            # search for the string
            result = await Youtube.searchVideos(self, query)
            print(result)
            applicant = context.author
            title = result["title"]
            artist = result["channel"]["name"]
            try:
                duration = result["duration"].split(":")
                duration.reverse()
                duration_sec = 0
                for i in range(len(duration)):
                    duration_sec = duration_sec + int(duration[i])*(60**i)
            except:
                duration_sec = 0
            thumbnail = result["thumbnails"][len(
                result["thumbnails"])-1]["url"]
            url = result["link"]

            print(applicant)
            print(queue.size)

            song = Song(applicant, title, artist, duration_sec,
                        url, "YouTube", thumbnail)
            await queue.addEntry(song)
        return 0

    @commands.command(aliases=['np', 'en lecture'])
    async def nowplaying(self, context):
        guild = context.guild
        if guild not in Queues:
            return await context.send('Rien en lecture')

        current = time_format(Queues[guild].elapsedtime)
        duration = time_format(
            Queues[guild].content[Queues[guild].cursor].duration)
        thumbnail = Queues[guild].content[Queues[guild].cursor].thumbnail

        await context.send('En lecture : %s\nProgression : %s / %s\n%s' % (Queues[guild].content[Queues[guild].cursor].title, current, duration, thumbnail))

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

    @commands.command(aliases=['arreter'])
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
