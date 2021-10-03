# dj-patrick

Made with Python 3.9  
In alpha early development

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
    "workdir": "downloads/",
    "discord-token": "<token>"
}
```
Put the json above in a config.json file in the following location using your favorite text editor (e.g. nano)
```bash
sudo -u dj-patrick nano /var/lib/dj-patrick/config.json
```

If you want to enable adding music from spotify , add the following lines to the config.json to make it look like that  

You can create a spotify application by going here https://developer.spotify.com/dashboard/applications
```json
{
    "prefix": "$",
    "workdir": "downloads/",
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
Edit the dj-patrick.service file by replacing \<user> and \<group> by dj-patrick (or the username you chose)
```md
User=<user>
Group=<group>
```
And then install the service
```bash
sudo cp dj-patrick.service /etc/systemd/system
sudo cp -r ../my-discord-bot /opt/dj-patrick
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