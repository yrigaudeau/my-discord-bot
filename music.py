import asyncio
import os
import discord
from discord.ext import commands
from youtube import Youtube
from spotify import Spotify
from help import Help
from config import Config, DLDIR
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


async def download_progress(filename, message, text, data):
    # 2.5 to estimate full file size
    downloadSize = data['formats'][0]['filesize']/1000000*2.5
    attempts = 0
    while not os.path.isfile(filename + ".part"):
        attempts += 1
        if attempts == 5:
            return
        await asyncio.sleep(1)

    while os.path.isfile(filename + ".part"):
        try:
            currentSize = os.path.getsize(filename + ".part")/1000000
        except:
            break
        await message.edit(content="%s [%.2f/%.2f Mo]" % (text, currentSize, downloadSize))
        await asyncio.sleep(1)


class Entry():
    def __init__(self, filename, applicant, entryType, fileSize=0, playlist=None):
        self.applicant = applicant
        self.filename = filename
        self.entryType = entryType
        self.fileSize = fileSize
        self.playlist = playlist

    def buildMetadataYoutube(self, data):
        #self.title = data['track'] if 'track' in data else data['title']
        self.title = data['title']
        #self.artist = data['artist'] if 'artist' in data else data['channel']
        self.artist = data['channel']
        self.album = data['album'] if 'album' in data else None
        self.duration = data['duration']
        self.thumbnail = data['thumbnail']
        self.id = data['id']
        self.url = 'https://www.youtube.com/watch?v=' + self.id


class Playlist():
    def buildMetadataYoutube(self, data):
        self.title = data['title']
        self.uploader = data['uploader'] if 'uploader' in data else None
        self.id = data['id']
        self.url = 'https://www.youtube.com/playlist?list=' + self.id


class Queue():
    def __init__(self, voice_client, text_channel, repeat_mode="none"):
        self.content = []
        self.size = 0
        self.cursor = 0
        self.starttime = 0
        self.voice_client = voice_client
        self.text_channel = text_channel
        self.repeat_mode = repeat_mode  # none, entry, playlist, all

    async def startPlayback(self):
        entry = self.content[self.cursor]
        filename = DLDIR + entry.filename if entry.entryType != "Direct" else entry.filename
        player = discord.FFmpegPCMAudio(filename, options="-vn")
        self.voice_client.play(player, after=lambda e: self.nextEntry())
        self.starttime = time.time()

        await self.text_channel.send('En lecture : %s' % (entry.title))

    def nextEntry(self):
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
                        print(i)
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
            print("voice client not none")
        else:
            voiceClient = await authorVoice.channel.connect(timeout=600, reconnect=True)
            print("voice client none")

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
            if not Config.spotifyEnabled:
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

        if query.startswith("http") and not query.startswith(("https://youtu.be", "https://www.youtube.com", "https://youtube.com")):
            # Other streams
            pass
        else:
            # Search YouTube
            if not query.startswith("https://"):
                message = await context.send("Recherche de \"%s\"..." % query)
                try:
                    result = await Youtube.searchVideos(query)
                except:
                    return await message.edit(context='Aucune musique trouvé')
                url = result["link"]
                print(url)
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
                    if data['entries'][i]['is_live'] == True:
                        filename = data['entries'][i]['url']
                    else:
                        try:
                            filename = Youtube.getFilename(data['entries'][i])
                            text = "Téléchargement de %s... (%d/%d)" % (data['entries'][i]['title'], i+1, len(data['entries']))
                            await asyncio.gather(
                                Youtube.downloadAudio(data['entries'][i]['webpage_url']),
                                download_progress(DLDIR + filename, message, text, data['entries'][i])
                            )
                        except:
                            await message.edit(content="Erreur lors du téléchargement de %s" % data['entries'][i]['title'])
                            continue
                        fileSize = os.path.getsize(DLDIR + filename)
                    entryType = "Direct" if filename.startswith("https://") else "Vidéo"
                    entry = Entry(filename, applicant, entryType, fileSize, playlist)
                    entry.buildMetadataYoutube(data['entries'][i])
                    await queue.addEntry(entry, queue_start + i)
                    await message.edit(content="%s a été ajouté à la file d\'attente" % data['entries'][i]['title'])
            else:
                if data['is_live'] == True:
                    filename = data['url']
                    fileSize = 0
                else:
                    try:
                        filename = Youtube.getFilename(data)
                        text = "Téléchargement de %s..." % data['title']
                        await asyncio.gather(
                            Youtube.downloadAudio(data['webpage_url']),
                            download_progress(DLDIR + filename, message, text,  data)
                        )
                    except:
                        return await message.edit(content="Erreur lors du téléchargement de %s" % data['title'])
                    fileSize = os.path.getsize(DLDIR + filename)
                entryType = "Direct" if filename.startswith("https://") else "Vidéo"
                # elif 'Music' in data['categories']:
                #    entryType = "Musique"
                entry = Entry(filename, applicant, entryType, fileSize)
                entry.buildMetadataYoutube(data)
                await queue.addEntry(entry)
                await message.edit(content="%s a été ajouté à la file d\'attente" % data['title'])

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
            title = entry.title
            artist = entry.artist
            album = entry.album
            url = entry.url
            entryType = entry.entryType
            image = entry.thumbnail
            applicant = entry.applicant

            current = time_format(int(time.time() - Queues[guild].starttime))
            duration = time_format(entry.duration)

            content = "Chaîne : %s\n" % (artist)
            if Queues[guild].cursor == index:
                content += "Progression : %s / %s\n" % (current, duration)
            if album is not None:
                content += "Album : %s\n" % (album)
            content += "Type : %s\n" % (entryType)
            content += "Position : %d" % index

            embed = discord.Embed(
                title=title,
                url=url,
                description=content,
                color=0x565493
            )
            if Queues[guild].cursor == index:
                name = "En cours de lecture"
                if not voiceClient.is_playing():
                    name = "En pause"
            else:
                name = "Informations piste"
            embed.set_author(name=name, icon_url="https://i.imgur.com/C66eNWB.jpg")
            embed.set_image(url=image)
            # embed.set_thumbnail(url="https://i.imgur.com/C66eNWB.jpg")
            embed.set_footer(text="Demandé par %s" % applicant.display_name, icon_url=applicant.avatar_url_as())

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
    async def remove(self, context, index: int = None):
        guild = context.guild.id
        voiceClient = context.voice_client
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')

        if index is None:
            return await context.send(embed=Help.get(context, 'music', 'remove'))

        if index < Queues[guild].size and index >= 0:
            entry = Queues[guild].getEntry(index)
            Queues[guild].removeEntry(index)
            if index <= Queues[guild].cursor:
                Queues[guild].cursor -= 1
            if index == Queues[guild].cursor:
                voiceClient.stop()
            if entry.entryType != "Direct" and entry.filename in os.listdir(DLDIR):
                os.remove(DLDIR + entry.filename)
            return await context.send('%s a bien été supprimé' % (entry.title))
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
            for entry in Queues[guild].content:
                if entry.entryType != "Direct" and entry.filename in os.listdir(DLDIR):
                    os.remove(DLDIR + entry.filename)
            Queues.pop(guild)
            voiceClient.stop()
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

    @commands.command(aliases=['g', 'go', ''])
    async def goto(self, context, index: int = None):
        guild = context.guild.id
        voiceClient = context.voice_client
        if guild not in Queues:
            return await context.send('Aucune liste d\'attente')

        if index is None:
            return await context.send(embed=Help.get(context, 'music', 'goto'))

        if index < Queues[guild].size and index >= 0:
            Queues[guild].cursor = index - 1
            voiceClient.stop()
            return #await context.send('Direction la musique n°%d' % index)
        else:
            return await context.send('L\'index %d n\'existe pas' % index)
