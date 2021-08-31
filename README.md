# my-discord-bot

In alpha early development

## Installation

### Clone repo and install dependencies
```bash
apt install python3 python3-pip ffmpeg git
git clone https://github.com/yrigaudeau/my-discord-bot.git
cd my-discord-bot
pip install requirements.txt
```

### Run
```bash
python3 .
```

### Install as service
```bash
cp my-discord-bot.service /etc/systemd/system
systemctl enable my-discord-bot
systemctl start my-discord-bot
```