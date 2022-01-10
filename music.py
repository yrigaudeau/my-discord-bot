import asyncio
import os
import discord
from discord.ext import commands
from youtube import Youtube
from spotify import Spotify
from help import Help
from config import config, DLDIR
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
    def __init__(self, filename, applicant, fileSize=0, playlist=None):
        self.applicant = applicant
        self.filename = filename
        self.fileSize = fileSize
        self.playlist = playlist

    def buildMetadataYoutube(self, data):
        self.title = data['title']
        self.channel = data['channel']
        self.channel_url = data['channel_url']
        self.album = data['album'] if 'album' in data else None
        self.duration = data['duration'] if self.fileSize != 0 else 0
        self.thumbnail = data['thumbnail']
        self.id = data['id']
        self.url = data['webpage_url']


class Playlist():
    def buildMetadataYoutube(self, data):
        self.title = data['title']
        self.uploader = data['uploader'] if 'uploader' in data else None
        self.id = data['id']
        self.url = data['webpage_url']

    def buildMetadataSpotify(self, data):
        pass


class Queue():
    def __init__(self, voice_client, text_channel, repeat_mode="none"):
        self.content = []
        self.size = 0
        self.cursor = 0
        self.starttime = 0
        self.voice_client = voice_client
        self.text_channel = text_channel
        self.repeat_mode = repeat_mode  # none, entry, playlist, all
        self.repeat_bypass = False

    async def startPlayback(self):
        if self.voice_client.is_connected() and not self.voice_client.is_playing():
            entry = self.content[self.cursor]
            filename = DLDIR + entry.filename if entry.fileSize != 0 else entry.filename
            player = discord.FFmpegPCMAudio(filename, options="-vn")
            self.voice_client.play(player, after=lambda e: self.nextEntry())
            self.starttime = time.time()

            await self.text_channel.send('En lecture : %s' % (entry.title))

    def nextEntry(self):
        if self.repeat_bypass is False:
            if self.repeat_mode == "none":
                self.cursor = self.cursor + 1
            elif self.repeat_mode == "entry":
                pass
            elif self.repeat_mode == "all":
                if self.cursor == self.size - 1:
                    self.cursor = 0
                else:
                    self.cursor = self.cursor + 1
            elif self.repeat_mode == "playlist":
                # A faire
                def gotostart():
                    i = self.cursor-1
                    while self.content[i].playlist is not None and i >= 0:
                        if self.content[i].playlist.id == current_entry.playlist.id:
                            i = i-1
                        else:
                            break
                    self.cursor = i

                # Fin de la playlist ??
                current_entry = self.content[self.cursor]
                if current_entry.playlist.id is not None:
                    if self.cursor < self.size-1:
                        if self.content[self.cursor+1].playlist is not None:
                            if self.content[self.cursor+1].playlist.id != current_entry.playlist.id:
                                # GO au début
                                gotostart()
                        else:
                            gotostart()
                    elif self.cursor == self.size - 1:
                        gotostart()

                self.cursor = self.cursor + 1

        self.repeat_bypass = False
        print("next")
        if self.cursor < self.size:
            coro = self.startPlayback()
            fut = asyncio.run_coroutine_threadsafe(coro, self.voice_client.loop)
            try:
                fut.result()
            except:
                print("coro error")

    async def addEntry(self, entry, position=None):
        if position is None or position == self.size:
            self.content.append(entry)
        else:
            self.content.insert(position, entry)
        self.size = self.size + 1
        if self.size == self.cursor + 1:
            await self.startPlayback()

        return position or self.size-1

    def removeEntry(self, index):
        self.content.pop(index)
        self.size = self.size - 1

    def moveEntry(self, frm, to):
        entry = self.content[frm]
        self.content.pop(frm)
        self.content.insert(to, entry)

    def getIndex(self, entry):
        return self.content.index(entry)

    def getEntry(self, index):
        return self.content[index]


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['p', 'lire', 'jouer'])
    async def play(self, context, *, query: str = None):
        if query is None:
            return await context.send(embed=Help.get(context, 'music', 'play'))

        authorVoice = context.author.voice
        voiceClient = context.voice_client

        if authorVoice is None:
            return await context.send('Non connecté à un salon vocal')
        elif voiceClient is not None:
            await voiceClient.move_to(authorVoice.channel)
            # print("voice client not none")
        else:
            voiceClient = await authorVoice.channel.connect(timeout=600, reconnect=True)
            # print("voice client none")

        guild = context.guild.id
        if guild not in Queues:
            Queues[guild] = Queue(voiceClient, context.channel)

        queue = Queues[guild]
        entry = None

        if query.startswith("www."):
            query = "https://" + query
            if context.author.id == 289086025442000896:
                await context.send("Mael t'abuse à mettre des liens en www, mais j'accepte quand même")

        if query.startswith(("spotify:", "https://open.spotify.com/")):
            if not config.spotifyEnabled:
                return await context.send('La recherche Spotify n\'a pas été configurée')
            if query.startswith("https://open.spotify.com/"):
                query = query[len("https://open.spotify.com/"):].replace('/', ':')
            else:
                query = query[len("spotify:"):]

            try:
                [_type, _id] = query.split(':')
                # Spotify link
                if _type == 'track':
                    track = Spotify.getTrack(_id)
                    query = "%s %s" % (track['name'], track['artists'][0]['name'])
                elif _type == 'playlist':
                    return await context.send('Fonction non prise en charge pour le moment')
            except:
                return await context.send('Le lien n\'est pas valide')

        if (query.startswith("http") or query.startswith("udp://") or query.startswith("tcp://")) and not query.startswith(("https://youtu.be", "https://www.youtube.com", "https://youtube.com")):
            # Other streams
            entry = Entry(query, context.author)
            position = await queue.addEntry(entry)
            await context.send("%d: %s a été ajouté à la file d\'attente" % (position, query))
        else:
            # Search YouTube
            if not query.startswith("https://"):
                message = await context.send("Recherche de \"%s\"..." % query)
                try:
                    result = await Youtube.searchVideos(query)
                except:
                    return await message.edit(content='Aucune musique trouvé')
                url = result["link"]
                # print(url)
            else:
                message = await context.send("Investigation sur \"%s\"..." % query[8:])
                url = query

            try:
                data = await Youtube.fetchData(url, self.bot.loop)
                print(data['webpage_url'])
            except:
                return await context.send('Le lien n\'est pas valide')

            applicant = context.author
            if 'entries' in data:
                playlist = Playlist()
                playlist.buildMetadataYoutube(data)
                queue_start = Queues[guild].size
                for i in range(len(data['entries'])):
                    if "is_live" in data['entries'][i]:
                        if data['entries'][i]['is_live'] == True:
                            filename = data['entries'][i]['url']
                            fileSize = 0
                        else:
                            try:
                                filename = Youtube.getFilename(data['entries'][i])
                                text = "(%d/%d) Téléchargement de %s..." % (i+1, len(data['entries']), data['entries'][i]['title'])
                                await Youtube.downloadAudio(data['entries'][i]['webpage_url'], message, text, self.bot.loop),
                            except:
                                await message.edit(content="Erreur lors du téléchargement de %s" % data['entries'][i]['title'])
                                continue
                            fileSize = os.path.getsize(DLDIR + filename)

                        if voiceClient.is_connected():
                            entry = Entry(filename, applicant, fileSize, playlist)
                            entry.buildMetadataYoutube(data['entries'][i])
                            position = await queue.addEntry(entry, queue_start + i)
                            if i == len(data['entries']) - 1:
                                await message.edit(content="%s a été ajouté à la file d\'attente" % data['title'])
                            else:
                                await message.edit(content="(%d/%d) %d: %s a été ajouté à la file d\'attente" % (i+1, len(data['entries']), position, data['entries'][i]['title']))
                        else:
                            await message.edit(content="Téléchargement annulé")
                            break
            else:
                if data['is_live'] == True:
                    filename = data['url']
                    fileSize = 0
                else:
                    try:
                        filename = Youtube.getFilename(data)
                        text = "Téléchargement de %s..." % data['title']
                        await Youtube.downloadAudio(data['webpage_url'], message, text, self.bot.loop),
                    except:
                        return await message.edit(content="Erreur lors du téléchargement de %s" % data['title'])
                    fileSize = os.path.getsize(DLDIR + filename)

                if voiceClient.is_connected():
                    entry = Entry(filename, applicant, fileSize)
                    entry.buildMetadataYoutube(data)
                    position = await queue.addEntry(entry)
                    await message.edit(content="%d: %s a été ajouté à la file d\'attente" % (position, data['title']))

    @commands.command(aliases=['np', 'en lecture'])
    async def nowplaying(self, context):
        guild = context.guild.id
        if guild not in Queues or Queues[guild].cursor == Queues[guild].size:
            return await context.send('Rien en lecture')
        else:
            await self.info(context, Queues[guild].cursor)

    @commands.command(aliases=['i'])
    async def info(self, context, index: int = None):
        guild = context.guild.id
        voiceClient = context.voice_client
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')

        if index is None:
            return await context.send(embed=Help.get(context, 'music', 'info'))

        if index < Queues[guild].size and index >= 0:
            entry = Queues[guild].content[index]

            content = "Chaîne : [%s](%s)\n" % (entry.channel, entry.channel_url)
            if Queues[guild].cursor == index:
                current = time_format(int(time.time() - Queues[guild].starttime))
                if entry.duration == 0:
                    content += "Progression : %s\n" % (current)
                else:
                    content += "Progression : %s / %s\n" % (current, time_format(entry.duration))
            if entry.album is not None:
                content += "Album : %s\n" % (entry.album)
            if entry.playlist is not None:
                content += "Playlist : [%s](%s)\n" % (entry.playlist.title, entry.playlist.url)
            content += "Position : %d" % index

            embed = discord.Embed(
                title=entry.title,
                url=entry.url,
                description=content,
                color=0x565493
            )
            if Queues[guild].cursor == index:
                name = "En cours de lecture"
                if voiceClient.is_paused():
                    name = "En pause"
            else:
                name = "Informations piste"
            embed.set_author(name=name, icon_url="https://i.imgur.com/C66eNWB.jpg")
            embed.set_image(url=entry.thumbnail)
            # embed.set_thumbnail(url="https://i.imgur.com/C66eNWB.jpg")
            embed.set_footer(text="Demandé par %s" % entry.applicant.display_name, icon_url=entry.applicant.avatar_url_as())

            return await context.send(embed=embed)
        else:
            return await context.send('L\'index %d n\'existe pas' % (index))

    @commands.command(aliases=['q', 'file'])
    async def queue(self, context):
        guild = context.guild.id
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')

        totalDuration = 0
        totalSize = 0
        current_playlist = ""
        list = ""
        for i in range(Queues[guild].size):
            entry = Queues[guild].content[i]
            if entry.playlist is not None:
                tab = "⠀⠀⠀⠀"
                if entry.playlist.id != current_playlist:
                    current_playlist = entry.playlist.id
                    if Queues[guild].repeat_mode == "playlist":
                        list += "⟳⠀ Playlist : %s\n" % entry.playlist.title
                    else:
                        list += "⠀⠀ Playlist : %s\n" % entry.playlist.title
            else:
                tab = ""
                current_playlist = ""
            totalDuration += entry.duration
            totalSize += entry.fileSize
            indicator = "⠀⠀ "
            if Queues[guild].cursor == i:
                if Queues[guild].repeat_mode == "entry":
                    indicator = "⟳⠀"
                else:
                    indicator = "→⠀"

            list += "%s%s%d: %s - %s - %.2fMo\n" % (tab, indicator, i, entry.title, time_format(entry.duration), entry.fileSize/1000000)

        repeat_text = {
            "none": "Aucun",
            "entry": "Musique en cours",
            "all": "Tout",
            "playlist": "Playlist"
        }

        embed = discord.Embed(
            description=list,
            color=0x565493
        )
        embed.set_author(name="Liste de lecture", icon_url="https://i.imgur.com/C66eNWB.jpg")
        embed.set_footer(text="Nombre d'entrées : %d | Mode de répétition : %s\nDurée totale : %s | Taille totale : %.2fMo" %
                         (Queues[guild].size, repeat_text[Queues[guild].repeat_mode], time_format(totalDuration), totalSize/1000000))

        return await context.send(embed=embed)

    @commands.command(aliases=['mv', 'déplacer'])
    async def move(self, context, frm: int = None, to: int = None):
        guild = context.guild.id
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')

        if frm is None or to is None:
            return await context.send(embed=Help.get(context, 'music' 'move'))

        if frm == to:
            return await context.send('La destination ne peut pas être égale à la source')

        if frm < Queues[guild].size and frm >= 0 and to < Queues[guild].size and to >= 0:
            title = Queues[guild].getEntry(frm).title
            Queues[guild].moveEntry(frm, to)
            return await context.send('%s a été déplacé de %d vers %d' % (title, frm, to))
        else:
            return await context.send('Une des deux positions est invalide')

    @commands.command(aliases=['rm', 'supprimer', 'enlever'])
    async def remove(self, context, option: str = None, index: int = None):
        guild = context.guild.id
        voiceClient = context.voice_client
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')

        if index is None and option is None:
            return await context.send(embed=Help.get(context, 'music', 'remove'))

        if index is None and option.isdigit():
            index = int(option)
        elif index is not None:
            pass
        else:
            return await context.send(embed=Help.get(context, 'music', 'remove'))

        if option == "-r":
            # go to end

            # remove entries
            return await context.send("Non pris en charge pour le moment")

        if index < Queues[guild].size and index >= 0:
            entry = Queues[guild].getEntry(index)
            Queues[guild].removeEntry(index)
            if index == Queues[guild].cursor:
                voiceClient.stop()
            if index <= Queues[guild].cursor:
                Queues[guild].cursor -= 1
            if entry.filename in os.listdir(DLDIR):
                os.remove(DLDIR + entry.filename)
            return await context.send('%s a bien été supprimé' % (entry.title))
        else:
            return await context.send('L\'index %d n\'existe pas' % (index))

    @commands.command(aliases=['s', 'passer'])
    async def skip(self, context):
        voiceClient = context.voice_client
        guild = context.guild.id
        if voiceClient is not None:
            if Queues[guild].cursor < Queues[guild].size:
                Queues[guild].repeat_bypass = True
                Queues[guild].cursor = Queues[guild].cursor + 1
                voiceClient.stop()
            else:
                return await context.send('Rien à passer')
        else:
            return await context.send('Aucune lecture en cours')

    @commands.command(aliases=['pauser', 'suspendre', 'uspendre', 'halte'])
    async def pause(self, context):
        voiceClient = context.voice_client
        if voiceClient is not None:
            if voiceClient.is_playing():
                voiceClient.pause()
                return await context.send('Mis en pause')
            else:
                return await context.send('Déjà en pause')
        else:
            return await context.send('Aucune lecture en cours')

    @commands.command(aliases=['reprendre'])
    async def resume(self, context):
        voiceClient = context.voice_client
        if voiceClient is not None:
            if voiceClient.is_paused():
                voiceClient.resume()
                return await context.send('Reprise de la lecture')
            else:
                return await context.send('Déjà en lecture')
        else:
            return await context.send('Aucune lecture en cours')

    @commands.command(aliases=['arreter', 'stopper', 'quitter', 'leave', 'hutup', 'top'])
    async def stop(self, context):
        voiceClient = context.voice_client
        guild = context.guild.id
        if voiceClient is not None:
            if guild in Queues:
                Queues.pop(guild)
            voiceClient.stop()
            for entry in Queues[guild].content:
                if entry.filename in os.listdir(DLDIR):
                    os.remove(DLDIR + entry.filename)
            await voiceClient.disconnect()
            return await context.send('Arrêté')
        else:
            return await context.send('Aucune lecture en cours')

    @commands.command(aliases=['r', 'repeter'])
    async def repeat(self, context, mode: str = None):
        guild = context.guild.id
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')

        repeat_modes = ["none", "entry", "all", "playlist"]
        if mode is not None:
            if mode not in repeat_modes:
                return await context.send(embed=Help.get(context, 'music', 'repeat'))
            else:
                new_mode = mode
                Queues[guild].repeat_mode = new_mode
        else:
            old_mode = Queues[guild].repeat_mode
            new_mode = repeat_modes[(repeat_modes.index(old_mode) + 1) % len(repeat_modes)]
            Queues[guild].repeat_mode = new_mode

        return await context.send('Le mode de répétition à été changé sur %s' % new_mode)

    @commands.command(aliases=['g', 'go'])
    async def goto(self, context, index: int = None):
        guild = context.guild.id
        voiceClient = context.voice_client
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')

        if index is None:
            return await context.send(embed=Help.get(context, 'music', 'goto'))

        if index < Queues[guild].size and index >= 0:
            Queues[guild].cursor = index
            if context.voice_client.is_playing() or context.voice_client.is_paused():
                Queues[guild].repeat_bypass = True
                voiceClient.stop()
            else:
                await Queues[guild].startPlayback()
            return  # await context.send('Direction la musique n°%d' % index)
        else:
            return await context.send('L\'index %d n\'existe pas' % index)
