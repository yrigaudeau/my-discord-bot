from FoxDot import *
import FoxDot
import re
from discord.ext import commands

# https://realpython.com/python-eval-function/

ALLOWED_NAMES = {
    **{
        k: v for k, v in Clock.__dict__.items() if not k.startswith("__")
    },
    **{
        k: v for k, v in Player.__dict__.items() if not k.startswith("__")
    },
    **{
        k: v for k, v in FoxDot.__dict__.items() if not k.startswith("__")
    },
    'print': print
}

foxdot_started = False
class Foxdot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def foxdot(self, context, query: str = None):
        global foxdot_started
        if query == "start":
            foxdot_started = True
        elif query == "stop":
            foxdot_started = False
            Clock.clear()
        else:
            await context.send("erreur")

    async def play_music(self, channel, instruction):
        play_pattern = re.compile("^[a-z][a-z0-9](\ |)>>")
        try:
            if(re.search(play_pattern, instruction)):
                code = compile(instruction, "<string>", "eval")
            else:
                code = compile(instruction, "<string>", "exec")
            # Validate allowed names
            for name in code.co_names:
                if name not in ALLOWED_NAMES:
                    raise NameError("L'utilisation de %s n'est pas autorisé" % name)

            result = eval(code, {"__builtins__": {}}, ALLOWED_NAMES)
            print(result)
            if result is not None:
                await channel.send(result)
        except SyntaxError as e:
            print(e)
            await channel.send(e)
        except NameError as e:
            print(e)
            await channel.send(e)
        except TypeError as e:
            print(e)
            await channel.send(e)
        except AttributeError as e:
            print(e)
            await channel.send(e)

    @classmethod
    async def process_foxdot(self, message):
        global foxdot_started
        if foxdot_started is True:
            await self.play_music(self, message.channel, message.content)
