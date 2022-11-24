import asyncio
import discord
import youtube_dl
import os
import sys
import time
from discord.ext import commands
from discord import ClientException
from discord import app_commands
from src import save
from src import bullybot
from src.ui import ui


voice_clients = {}

yt_dl_opts = {'format': 'bestaudio/best'}
ytdl = youtube_dl.YoutubeDL(yt_dl_opts)

ffmpeg_options = {'options': "-vn"}

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
u = ui()


#############################    CLIENT EVENTS    #############################


# This event happens when a message gets sent
@client.command()
async def play(msg):

    try:
        voice_client = await msg.author.voice.channel.connect()
        voice_clients[voice_client.guild.id] = voice_client
    except:
        print("error")

    try:
        url = msg.message.content.split()[1]

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

        song = data['url']
        player = discord.FFmpegPCMAudio(song, **ffmpeg_options)

        voice_clients[msg.guild.id].play(player)

    except Exception as err:
        print(err)


@client.command()
async def pause(msg):
    try:
        voice_clients[msg.guild.id].pause()
    except Exception as err:
        print(err)

@client.command()
async def resume(msg):
    try:
        voice_clients[msg.guild.id].resume()
    except Exception as err:
        print(err)

    
@client.command()
async def stop(msg):
    try:
        voice_clients[msg.guild.id].stop()
        await voice_clients[msg.guild.id].disconnect()
    except Exception as err:
        print(err)

# METHOD: on_ready()
# PURPOSE: executes once the client/bot has booted.
@client.event
async def on_ready():
    try:
        synced = await client.tree.sync()
        client.loop.create_task(status_task())    
        print("Synced: {}".format(synced))
    except ClientException:
        print("Failed to sync")
    




@client.tree.command(name="hello")
async def hello(ctx: discord.Interaction):
    await ctx.response.send_message(f"Hello {ctx.user.mention}!", ephemeral=True)


@client.tree.command(name="speak")
@app_commands.describe(arg="What should the bot say?")
async def speak(ctx: discord.Interaction, arg: str):
    await ctx.response.send_message(arg, ephemeral=True)


#  METHOD: on_message()
# PURPOSE: For every given message sent into a channel, on_message
#          will be called, and the bot will react accordingly
@client.event
async def on_message(message):
    if message.author != client.user:
        await client.process_commands(message)



#  METHOD: on_voice_state_update
# PURPOSE: For every change in user voice state (mute, deafen, etc), 
#          on_voice_state_update is triggered. 
@client.event
async def on_voice_state_update(member, before, after):
    if not after.afk and member.id == 253874297066618880:
        ctx = member.guild.voice_client
        print(colors.OKCYAN + "User joined a channel.")
        
        if ctx is None:
            print(colors.WARNING + "Im not in the channel when they joined")
        else:
            print(colors.OKCYAN + "I am in the channel")
    else:
        pass



#  METHOD: status_task()
# PURPOSE: Is called on a loop from on_ready, and allows certain methods
#          to be asynchronously called during execution
async def status_task():
    while True:
        await asyncio.sleep(1)
        



#############################   CLIENT COMMANDS   #############################


# ---------------------------
#      VOICE CHANNELS
# ---------------------------


#  METHOD: follow
# PURPOSE: Allows the user to specify what channel the bot should join
#          based off the provided ID
@client.command()
async def join(ctx):
    try:
        voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
        if(voice_client):
            await voice_client.disconnect()

        print(ctx.message.author.voice.channel)
        voiceChannel=ctx.message.author.voice.channel
        await voiceChannel.connect()
    except ClientException:
        print(colors.FAIL + "Client Exception: Is the caller in a channel?" + colors.ENDC)

@client.command()
async def leave(ctx):
    voice_client = discord.utils.get(client.voice_clients, guild=ctx.guild)
    if voice_client:
        await voice_client.disconnect()

#  METHOD: join
# PURPOSE: User can request that the bot joins the channel that they
#          are currently in. 
@client.command()
async def goto(ctx):
    try:
        guild = ctx.guild
        message = ctx.message.content[6:]
        voiceChannel=ctx.guild.get_channel(int(message))  

        if ctx.voice_client is None:
            await voiceChannel.connect()
        else:
            await ctx.voice_client.move_to(voiceChannel)
    except ClientException:
        print(colors.FAIL + "Client Exception thrown in join()")


@client.command()
async def ping(ctx):
    '''
    This text will be shown in the help command
    '''

    # Get the latency of the bot
    latency = client.latency  # Included in the Discord.py library
    # Send it to the user
    await ctx.send(latency)


# ---------------------------
#       SPEACH LOGIC 
# ---------------------------




# METHOD: say
# PURPOSE: Given that the bot is inside a VC, it will speak outloud given
#          the string provided by the user
@client.command()
async def say(ctx):
    try:    
        message = ctx.message.content
        command = 'espeak -p 10 -s 140 -a 1000 -ven-us --stdout "' + message[5:] + '" > message'
        os.system(command)
        f = open("message", "r")
        voice = discord.utils.get(client.voice_clients, guild=ctx.guild)
        voice.play(discord.FFmpegPCMAudio(f, executable="ffmpeg", pipe=True,
                stderr=None, before_options="-fflags discardcorrupt -guess_layout_max 0", options=None))
        f.close()
        print("Done")
    except AttributeError:
        print(colors.FAIL + "Not in a voice channel")


# ---------------------------
#      MESSAGE CONTROL 
# ---------------------------

#  METHOD: wordSleuth()
# PURPOSE: Given a word specified by the user, searches previous messages in that channel
#          and tallies them, returning the total to the user.
@client.command()
async def wordSleuth(ctx, sleuth):
    id = ctx.message.author.id
    counter = 0
    async for message in ctx.channel.history(limit=None):
        if sleuth.lower() in message.content.lower():
            if(message.author.id == id):
                counter = counter + message.content.count(sleuth)

    sleuthed = "You said the word " + sleuth + " " + str(counter) +" times."
    await printToChannel(ctx.message, sleuthed)




#  METHOD: deleteMe()
# PURPOSE: Deletes every messages sent by the calling user in the channel
#          that deleteMe() was called in.
@client.command()
async def deleteMe(ctx):
    id = ctx.message.author.id
    async for message in ctx.channel.history(limit=None):
        if(message.author.id == id):
            await message.delete()



#  METHOD: cleanBot()
# PURPOSE: Deletes every message sent by the bot in the calling channel.
@client.command()
async def cleanBot(ctx):
    async for message in ctx.channel.history(limit=None):
        if(message.author.id == 748778849751400871):
            await message.delete()


#  METHOD: deleteLast()
# PURPOSE: Similar to deleteMe(), but deletes <num> amount of users messages
#          and then stops. 
@client.command()
async def deleteLast(ctx, num):
    counter = 0
    id = ctx.message.author.id
    try:
        num = int(num) + 1
        if(num <= 100 and num > 0):
            async for message in ctx.channel.history(limit=num):
                if(message.author.id == id):
                    await message.delete()
        else:
            raise ValueError("Bad Int")

    except ValueError as ve:
        await printToChannelDelete(ctx.message, "You are an idiot.")


#  METHOD: saveMe()
# PURPOSE: Calls the save_me method in the save.py class
@client.command()
async def saveMe(ctx):
    await save.save_me(ctx)


#############################   BOT METHODS   #############################


#  METHOD: printToChannel
# PURPOSE: Yeah u now
async def printToChannel(message, text):
    await message.channel.send(text)


#  METHOD: printThenDelete
# PURPOSE: Send a message to a channel, delete after few secs
async def printThenDelete(message, text):
    await message.channel.send(text, delete_after = 3)


#  METHOD:
# PURPOSE:
async def bully(message):
    target = "example_uuid"
    uid = message.author.id
    if (uid == target):
        await bullybot.initBully(message)


    


class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    UNDERLINE = '\033[4m'


client.run(os.environ["DISCORD_TOKEN"])
