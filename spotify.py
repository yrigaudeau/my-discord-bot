import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config import Config

if Config.spotifyEnabled:
    SPOTIPY_CLIENT_ID = Config.conf['spotify-client-id']
    SPOTIPY_CLIENT_SECRET = Config.conf['spotify-client-secret']
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET))


class Spotify():
    def getTrack(url):
        try:
            return sp.track(url)
        except:
            return None


if __name__ == "__main__":
    track = Spotify.getTrack('https://open.spotify.com/track/3ERL0lPZqTNGCN6UGOjBsV?si=a111cb5f068546ef')
    print(track['name'], track['artists'][0]['name'])
