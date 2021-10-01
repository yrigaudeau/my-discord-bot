import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from config import Config

if Config.spotifyEnabled:
    SPOTIPY_CLIENT_ID = Config.conf['spotify-client-id']
    SPOTIPY_CLIENT_SECRET = Config.conf['spotify-client-secret']

class Spotify():
    def getSpotipy():
        auth_manager = SpotifyClientCredentials(SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)
        return spotipy.Spotify(auth_manager=auth_manager)

    @classmethod
    def getTrack(self, url):
        try:
            return self.getSpotipy().track(url)
        except:
            return None


if __name__ == "__main__":
    track = Spotify.getTrack('https://open.spotify.com/track/3ERL0lPZqTNGCN6UGOjBsV?si=a111cb5f068546ef')
    print(track['name'], track['artists'][0]['name'])