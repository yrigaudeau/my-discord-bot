import os
import json

class Config():
    def __init__(self):
        self.conf = None

    @classmethod
    def readConfig(self):
        f = open(os.path.dirname(os.path.realpath(__file__)) + "/config.json", 'r')
        self.conf = json.load(f)
        f.close()

    @classmethod
    def getPrefix(self, bot=None, message=None):
        return self.conf['prefix']

    @classmethod
    def setPrefix(self, prefix):
        self.conf['prefix'] = prefix
        f = open(os.path.dirname(os.path.realpath(__file__)) + "/config.json", 'w')
        json.dump(self.conf, f)
        f.close()


Config.readConfig()