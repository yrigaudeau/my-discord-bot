import os
import json

CFGFILE = "config.json"
DLDIR = "downloads/"

class Config():
    @classmethod
    def readConfig(self):
        if os.path.isfile(CFGFILE):
            f = open(CFGFILE, 'r')
            self.conf = json.load(f)
            f.close()
            if 'spotify-client-id' in self.conf and 'spotify-client-secret' in self.conf:
                self.spotifyEnabled = True
            else:
                self.spotifyEnabled = False
            self.token = self.conf['discord-token']
        else:
            print("Fichier config non trouvé ou non valide:", CFGFILE)
            exit(0)

    @classmethod
    def getPrefix(self):
        return self.conf['prefix']

    @classmethod
    def setPrefix(self, prefix):
        self.conf['prefix'] = prefix
        f = open(CFGFILE, 'w')
        json.dump(self.conf, f)
        f.close()


Config.readConfig()