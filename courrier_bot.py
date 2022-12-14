# This is a bot that will start with device boot and will
# give me the ip to ssh to when on a network w/o a static
# address

import discord
import subprocess
import re
import teuphlib
import logging
import time
import asyncio
import aiohttp
from datetime import datetime
from discord.ext import commands, tasks

intents = discord.Intents.all()
intents.presences = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    fmt='| {levelname} | {message}',
    style="{",
)

handler = logging.FileHandler(filename=f"watering.log")  # /home/qwire/teuph/watering.log
handler.setFormatter(formatter)
logger.addHandler(handler)

teuphlib.setup()

bot = commands.Bot(command_prefix=">", intents=intents)

bot.load_extension("jishaku")

@bot.event
async def on_ready():
    async with aiohttp.ClientSession() as ses:
        await ses.post("https://discord.com/api/webhooks/1050971265508319242/QwX_b1dvoCHf2XdnydJaowVpw9f9Ecpb9frcFcWoOHJwjLemSSfNHUAXy2GHHdyXH0IS", json={"content": f"🟢 online"})

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        await ctx.send("https://media.tenor.com/_tHxkI_ur48AAAAC/nuh-uh-nuh.gif")
    else:
        logger.warning(str(error))


def can_use():
    async def pred(ctx):
        return ctx.author.id in (719980255942541362, 849686750942068797)

    return commands.check(pred)


@tasks.loop(seconds=3600)
async def the_process():
    # fix code the pump doesn't stop if sensor is wet again.
    iters = 0
    now = datetime.utcnow().strftime("%H:%M:%S - %b %d %Y")
    logger.info(teuphlib.is_wet())
    if not teuphlib.is_wet():
        start = time.perf_counter()
        teuphlib.pump()
        while True:
            await asyncio.sleep(2)
            if not teuphlib.is_wet():
                break
            elif (iters := iters + 1) >= 5:
                # this means we've pumped for over 10 seconds.
                # cutting the water as a safeguard in case I
                # broke something
                break
        teuphlib.unpump()
        dur = round(time.perf_counter()-start, 1)
        logger.info(f"{now} - Poured water for {dur}s")
    else:
        logger.info(f"{now} - No dryness detected, nothing to do")

@bot.command()
@commands.is_owner()
async def start(ctx):
    the_process.start()
    await ctx.send("??")

@bot.command()
@commands.is_owner()
async def close(ctx):
    the_process.cancel()
    await ctx.send("??")

@bot.command()
async def wet(ctx):
    try:
        await ctx.send("yes" if teuphlib.is_wet() else "no")
        await ctx.send(teuphlib.is_wet())
    except Exception as e:
        await ctx.send(e)

@bot.command()
async def demo(ctx):
    class Menu(discord.ui.View):
        def enable_all_items(self):
            for i in self.children:
                i.disabled = False

        @discord.ui.button(label="Run the Pump", style=discord.ButtonStyle.grey)
        async def pump(self, btn: discord.ui.Button, inter: discord.Interaction):
            btn.style = discord.ButtonStyle.green
            btn.label = "Working..."
            self.disable_all_items()
            await inter.response.send_message(content="Pumping for 10 seconds...", ephemeral=True)
            await self.message.edit(view=self)
            teuphlib.pump()
            await asyncio.sleep(10)
            teuphlib.unpump()
            btn.style = discord.ButtonStyle.blurple
            btn.label = "Run the Pump"
            try:
                await inter.edit_original_response(content="Stopped pumping.")
            except:
                pass
            self.enable_all_items()
            await self.message.edit(view=self)

        @discord.ui.button(label="Ping Sensor", style=discord.ButtonStyle.grey)
        async def sensor(self, btn: discord.ui.Button, inter: discord.Interaction):
            btn.style = discord.ButtonStyle.green
            btn.label = "Working..."
            self.disable_all_items()
            listing = ""
            await inter.response.send_message(content="Pinging...", ephemeral=True)
            await self.message.edit(view=self)

            for i in range(1, 6):
                await asyncio.sleep(2)
                reading = "WET" if teuphlib.is_wet() else "DRY"
                listing += f"`reading {i}`: `{reading}`\n"
                await inter.edit_original_response(content=f"Pinging...\n\n{listing}")

            await asyncio.sleep(2)
            btn.style = discord.ButtonStyle.blurple
            btn.label = "Ping Sensor"
            try:
                await inter.edit_original_response(content=f"Pinging...\n\n{listing}\n\nDone reading")
            except:
                pass
            self.enable_all_items()
            await self.message.edit(view=self)

        @discord.ui.button(label="See Logs", style=discord.ButtonStyle.blurple)
        async def logs(self, btn: discord.ui.Button, inter: discord.Interaction):
            with open("watering.log", "r") as fp:
                entries = fp.readlines()[-10:]

            listing = "\n```"
            for c, e in enumerate(entries, start=1):
                listing = f"{c} {e}"+listing

            embed = discord.Embed(
                description=f"```\n{listing}",
                color=discord.Color.green()
            )

            await inter.response.send_message(embed=embed, ephemeral=True)

    embed = discord.Embed(
        title="Welcome to the Demo",
        description="Using the buttons bellow, you will be able to test out the different components of the Plant Humidifier.",
        color=discord.Color.green()
    )

    await ctx.send(embed=embed, view=Menu(timeout=None))



@bot.command()
@commands.is_owner()
async def hello(ctx):
    # Get the eSSID (network name)
    essid = subprocess.Popen(['iwgetid'], stdout=subprocess.PIPE).communicate()[0].decode('utf-8').split(":")[-1].rstrip("\n").strip('"')

    # Find the devices ip
    ifconfig = subprocess.Popen(['ifconfig'], stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    for i in re.findall('inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ifconfig):
        if i not in ("127.0.0.1", "255.0.0.0"):
            ip = i
            break

    text = f"""
Hi

ESSID: {essid}
ip: {ip}
"""

    await ctx.send(text)

with open("token.txt", "r") as fp:
    token = fp.read()

try:
    bot.run(token)
finally:
    teuphlib.shutdown()
