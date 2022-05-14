import discord
from discord.ext import tasks
from PIL import Image
import requests
from KARA import *
from load_gpt_forefront import *
from load_OFA import *
import os

token = os.getenv('BOT_TOKEN')
bot = discord.Client()
with open("example_chatlog.txt", "r") as f:
    initial_chatlog = f.read()

ofa = OFACore()
gpt = FFNEOX()
kara = Kara(initial_chatlog, "Kara", gpt, ofa)
new_response = None

first_message = True
last_channel = None

@tasks.loop(hours=1)
async def backup():
    with open("backup.txt", "w") as f:
        f.write(kara.chat_log)

@tasks.loop(seconds=30)
async def tickClock():
    global new_response, first_message
    if not first_message:
        print("tick")
        new_response = kara.tick()
        if new_response is not None:
            await last_channel.send(new_response)
            new_response = None
        if kara.decision_counter != 0:
            await bot.change_presence(status=discord.Status.idle)
        else:
            await bot.change_presence(status=discord.Status.online)

@bot.event
async def on_ready():
    print("Boot")


@bot.event
async def on_message(message):
    global new_response, first_message, last_channel
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
        content.replace(usr.mention, usr.name)
    print(content, author)
    kara.update_log(content, author)
    if bot.user.mentioned_in(message):
        new_response = kara.tick(force=True)
    last_channel = message.channel



tickClock.start()
backup.start()
bot.run(token)