from youtubesearchpython.__future__ import VideosSearch
import youtube_dl

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'dj-patrick/%(extractor)s-%(id)s-%(title)s.%(ext)s',
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
    async def searchVideos(query):
        videosSearch = VideosSearch(query, limit=1)
        videosResult = await videosSearch.next()
        return videosResult["result"][0]

    async def downloadAudio(url):
        data = ytdl.extract_info(url, download=False)
        if data['is_live'] == True:
            filename = data['url']
        else:
            data = ytdl.extract_info(url, download=True)
            filename = ytdl.prepare_filename(data)
        print(filename)
        return data, filename
