import os
import json

CFGFOLDER = os.path.expanduser('~') + "/.config/dj-patrick/"
CFGFILE = CFGFOLDER + "config.json"

class Config():
    def __init__(self):
        self.conf = None

    @classmethod
    def readConfig(self):
        if os.path.isfile(CFGFILE):
            f = open(CFGFILE, 'r')
            self.conf = json.load(f)
            f.close()
        else:
            print("Fichier config non trouvé:", CFGFILE)
            exit()

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