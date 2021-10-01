# my-discord-bot

Made with Python 3.9  
In alpha early development

# Installation

## Clone repo and install dependencies
```bash
apt install python3 python3-pip ffmpeg git
git clone https://github.com/yrigaudeau/my-discord-bot.git
cd my-discord-bot
pip install -r requirements.txt
```

## Create config file
```json
{
    "prefix": "$",
    "workdir": "/tmp/dj-patrick/",
    "token": "<your-token>"
}
```
Put the json above in a config.json file in the following location using your favorite text editor (e.g. nano)
```bash
mkdir -p ~/.config/dj-patrick
nano ~/.config/dj-patrick/config.json
```

## Run
```bash
python3 .
```

## Install as service
```bash
cp my-discord-bot.service /etc/systemd/system
cp -r ../my-discord-bot /opt
systemctl daemon-reload
systemctl enable my-discord-bot
systemctl start my-discord-bot
```

### Uninstall

```bash
systemctl disable my-discord-bot
systemctl stop my-discord-bot
rm /etc/systemd/system/my-discord-bot.service
systemctl daemon-reload
rm -r /opt/my-discord-bot
rm -r ~/.config/dj-patrick
```