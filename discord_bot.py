import discord
from discord.ext import tasks
from PIL import Image
import requests
from KARA import *
#from load_gpt_forefront import *
from load_customendpoint import *
from load_OFA import *
import os

token = os.getenv('BOT_TOKEN')
bot = discord.Client()
with open("example_chatlog.txt", "r") as f:
    initial_chatlog = f.read()

# the bot will only listen to commands by this username
OWNER = "Your-username-here"

ofa = OFACore()
gpt = CUSTMGPT()
kara = Kara(initial_chatlog, "Kara", gpt, ofa)
new_response = None

first_message = True
last_channel = None
time_left = 3


@tasks.loop(hours=1)
async def backup():
    print("Backed up")
    with open("backup.txt", "w") as f:
        f.write(kara.chat_log)


@tasks.loop(seconds=30)
async def tickClock():
    global new_response, first_message, time_left
    if not first_message:
        time_left -= 1
        print("tick")
        new_response = kara.tick()
        print(new_response)
        if new_response is not None:
            await last_channel.send(new_response)
            new_response = None
        if kara.decision_counter != 0:
            await bot.change_presence(status=discord.Status.idle)
        else:
            await bot.change_presence(status=discord.Status.online)
        if time_left == 0:
            print("Clock stopped")
            kara.chat_log += "\n"
            tickClock.cancel()


@bot.event
async def on_ready():
    print("Boot")
    for guild in bot.guilds:
        print(guild.name)
        for channel in guild.channels:
             if type(channel) != discord.CategoryChannel:
                try:
                    await channel.send("KARA STARTED, Flavour prompt: "+kara.flavour_prompt)
                except:
                    print("Forbidden")



@bot.event
async def on_message(message):
    global new_response, first_message, last_channel, time_left
    if message.author.name == OWNER:
        if message.content == "regenerate prompt":
            kara.update_flavour()
            await message.channel.send("NEW PROMPT: " + kara.flavour_prompt)
            return
    last_channel = message.channel
    if time_left == 0:
        print("Clock started again")
        first_message = True
        tickClock.start()
    time_left = 3
    if message.author == bot.user:
        return
    first_message = False
    server = message.guild
    author = message.author.display_name
    content = message.content
    if "https://" in content:
        url = content[content.find("https://"):]
        if url.find(" ") != -1:
            url = url[:url.find(" ")+1]
        extension = url.split('.')[-1].upper()
        if '?' in extension:
            extension = extension.split('?')[0]
        print(extension)
        print(url)
        im = Image.open(requests.get(url, stream=True).raw)
        kara.show(author, im, extension)
        print(kara.chat_log[-200])
    for attach in message.embeds:
        # this dont work
        print("Embed detected")
        im = attach.image.url
        if type(im) != discord.Embed.Empty:
            extension = im.split('.')[-1].upper()
            if '?' in extension:
                extension = extension.split('?')[0]
            im = Image.open(requests.get(im, stream=True).raw)
            kara.show(author, im, extension)
            print(kara.chat_log[-200])
    for attach in message.attachments:
        print("Attachment detected")
        extension = attach.filename.split('.')[1].upper()
        im = Image.open(requests.get(attach.url, stream=True).raw)
        kara.show(author, im, extension)
        print(kara.chat_log[-200])
    for usr in message.mentions:
        content = content.replace(usr.mention, usr.name)
    print(content, author)
    kara.update_log(content, author)
    if bot.user.mentioned_in(message):
        new_response = kara.tick(force=True)
        if new_response is not None:
            await message.channel.send(new_response)
        else:
            print("Error!")
        new_response = None


tickClock.start()
backup.start()
bot.run(token)