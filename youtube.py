from youtubesearchpython.__future__ import VideosSearch
import youtube_dl
import asyncio

from config import Config
WORKDIR = Config.conf['workDir']

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': WORKDIR + '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    # bind to ipv4 since ipv6 addresses cause issues sometimes
    'source_address': '0.0.0.0'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class Youtube():
    async def searchVideos(query, nbEntries=1):
        videosSearch = VideosSearch(query, limit=nbEntries)
        videosResult = await videosSearch.next()
        return videosResult["result"][0]

    async def fetchData(url, loop=None):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        return data

    def getFilename(data):
        filename = ytdl.prepare_filename(data)[len(WORKDIR):]
        print(filename)
        return filename

    async def downloadAudio(url, loop=None):
        loop = loop or asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))


if __name__ == "__main__":
    data = asyncio.run(Youtube.fetchData(
        "https://www.youtube.com/playlist?list=PLI_rLWXMqpSkAYfar0HRA7lykydwmRY_2"))
    #data, filename = asyncio.run(Youtube.downloadAudio("https://www.youtube.com/watch?v=WnqOhgI_8wA?list="))
    f = open('ex.json', 'w')
    f.write(str(data))
    f.close()
