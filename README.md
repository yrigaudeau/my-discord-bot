# my-discord-bot

In alpha early development

## Installation

### Clone repo and install dependencies
```bash
apt install python3 python3-pip ffmpeg git
git clone https://github.com/yrigaudeau/my-discord-bot.git
cd my-discord-bot
pip install -r requirements.txt
```

### Create config file
```json
{
    "prefix": "$",
    "token": "'your-token'"
}
```
Put the json above in a config.json file with your favorite text editor (e.g. nano)
```bash
nano config.json
```

### Run
```bash
python3 .
```

### Install as service
```bash
cp my-discord-bot.service /etc/systemd/system
cp -r ../my-discord-bot /opt
systemctl daemon-reload
systemctl enable my-discord-bot
systemctl start my-discord-bot
```