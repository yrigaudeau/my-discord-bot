# dj-patrick

Made with Python 3.9  
In alpha early development

# Unique Features

* Playlists
    * Playlists are identified in queue
    * Possibility to loop within a playlist
    * Possibility to remove all songs in a playlist

# Installation

## Clone repo and install dependencies
```bash
sudo apt install python3 python3-pip ffmpeg git
git clone https://github.com/yrigaudeau/my-discord-bot.git
cd my-discord-bot
pip install -r requirements.txt
```
## Running as user
It's recommended to run the python script as user on the system (not as root). You can run the bot on your current username or create a new one with home folder
```bash
sudo useradd -md /var/lib/dj-patrick dj-patrick
```

## Create config file
You can create a discord application by going here https://discord.com/developers/applications
```json
{
    "prefix": "$",
    "discord-token": "<token>"
}
```
Put the json above in a config.json file in the following location using your favorite text editor (e.g. nano)
```bash
sudo -u dj-patrick nano /var/lib/dj-patrick/config.json
```

If you want to enable adding music from spotify, add the following lines to the config.json to make it look like that  

You can create a spotify application by going here https://developer.spotify.com/dashboard/applications
```json
{
    "prefix": "$",
    "discord-token": "<token>",
    "spotify-client-id": "<id>",
    "spotify-client-secret": "<secret>"
}
```

## Run
```bash
sudo -u dj-patrick python3 .
```

## Install as service
```bash
sudo mv dj-patrick.service /etc/systemd/system
sudo mkdir /opt/dj-patrick
sudo cp * /opt/dj-patrick
sudo systemctl daemon-reload
sudo systemctl enable dj-patrick
sudo systemctl start dj-patrick
```

### Uninstall

```bash
sudo systemctl disable dj-patrick
sudo systemctl stop dj-patrick
sudo rm /etc/systemd/system/dj-patrick.service
sudo systemctl daemon-reload
sudo rm -r /opt/dj-patrick
sudo rm -r /var/lib/dj-patrick
```

# (Optionnal) FoxDot installation

## FoxDot
```
pip install FoxDot
```

## Jackd and Supercollider
```bash
apt install jackd supercollider alsa-utils
```