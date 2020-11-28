import discord
import logging
import re
import json
import asyncio

from discord.ext import commands

import time
from datetime import datetime, date, timedelta

import os
import sys

import psycopg2
from psycopg2 import Error

import requests
import io
from contextlib import redirect_stderr

import random 

from modules import checks, pk
from modules.HelpMenu import HBSHelpCommand
from modules.functions import splitLongMsg, formatTriggerDoc
from resources.constants import *

startup_extensions = ["Counters","Yeets","CommandErrorHandler","Starboards","DumbCommands","EmojiTracking","AdminCommands"]

DATABASE_URL = os.environ['DATABASE_URL']

bannedPhrases = ["Good Morning", "Good Mornin", "Good Evening", "Good Evenin", "Fair Enough", "Cool Thanks", "Mornin Fellas", "Evenin Fellas"]
starsList = ['｡', '҉', '☆', '°', ':', '✭', '✧', '.', '✼', '✫', '．', '*', '゜', '。', '+', 'ﾟ', '・', '･', '★']
spaces = [" " for x in range(30)]

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(
    command_prefix=("hbs;","\hbs;","hbs ","\hbs ","Hbs;","\Hbs;","Hbs ","\Hbs "),
    owner_ids=[VRISKA_ID, SKYS_ID, EM_ID],
    case_insensitive=True,
    help_command=HBSHelpCommand(indent=4,paginator=commands.Paginator()),
    description="HussieBot Oppression & More",
    status="online",
    #help_command=None,
    intents=intents)


# ----- Discord Events ----- #
@client.event
async def on_ready():
    #await client.get_channel(753349219808444438).send("We have logged in")
    sys.stdout.write('We have logged in as ')
    sys.stdout.write(client.user.name + " (" + str(client.user.id) + ")\n")
    sys.stdout.write("Discord Version " + str(discord.__version__) + "\n")
    sys.stdout.write('------\n')

    sys.stdout.write('Servers connected to: \n')
    for g in client.guilds:
        sys.stdout.write(g.name + ", Owner ID: " + str(g.owner_id) + "\n");

    sys.stdout.flush()

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vars WHERE name = 'game'")
    game = cursor.fetchall()[0][1]
    await client.change_presence(activity=discord.Game(name=game))

    conn.commit()
    cursor.close()
    conn.close()

@client.event
async def on_message(message: discord.Message):
    if (message.guild == None):
        return
        
    #HANDLE HUSSIEBOT VRISKA REACTS
    if message.author.id == HUSSIEBOT_ID: #if hussiebot
        if (message.content in ["<:vriska:480855644388458497>",":vriska:",":eye:"]): 
                await message.delete()
        for phrase in bannedPhrases:
            if message.content.find(phrase) != -1:
                await message.delete()
                break

    #PURGE STARBOARD IF LAST PURGE WAS > 7 DAYS AGO
    '''    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vars WHERE name = 'laststarboardpurge'")
    last_starboard_purge = datetime.strptime(cursor.fetchall()[0][1], '%Y-%m-%d %H:%M:%S.%f')
    
    currTime = datetime.utcnow()
    sys.stdout.write(str(currTime - last_starboard_purge) + " " + str(week))

    if (currTime - last_starboard_purge > week):
        starboards = client.get_cog('Starboards')

        cursor.execute("UPDATE vars set value = %s WHERE name = 'laststarboardpurge'", (currTime,))
        await starboards.purgeStarboards(currTime-week)

    conn.commit()
    cursor.close()
    conn.close()
        '''
    if (message.author.id != client.user.id) and (message.guild.id == SKYS_SERVER_ID) and (message.webhook_id == None):
        await client.get_cog('EmojiTracking').on_message_emojis(message)
            
    await client.process_commands(message)
                        
    
@client.event
async def on_raw_reaction_add(payload):
    if (payload.guild_id == None):
        return
    #HANDLE PK DELETION
    if payload.emoji.name == "❌":
        #GET CHANNEL AND MESSAGE
        channel = client.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        
        #REMOVE UNWANTED MESSAGES FROM BOTS
        if (msg.author.id in [HUSSIEBOT_ID, TODDBOT_ID, YAGBOT_ID, client.user.id]):
            await msg.delete()
        
        #REMOVE PK MESSAGES
        if payload.user_id != PLURALKIT_ID:
            system = await pk.get_pk_system_from_userid(payload.user_id)
            
            if system != None:
                
                system = system["id"]

                reacts = msg.reactions
                users = [await react.users().flatten() for react in reacts if react.emoji == "✅"]
                pk_check_reacts = [user for user in users if user.id == pluralkit_id]

                if not len(pk_check_reacts) > 0:
                    for embed in msg.embeds:
                        emb = json.dumps(embed.to_dict())
                        if (emb.find(system) != -1): #IF SYSTEM ID FOUND IN EMBED
                            await msg.edit(suppress=True)
                            await msg.clear_reactions()
                            msgDel = client.get_emoji(767960168444723210)
                            await msg.add_reaction(msgDel)


@client.command(pass_context=True,brief="Spoil an image.")
async def spoil(ctx, *, text=""):
    
    files = []
    for a in ctx.message.attachments:
        file = await a.to_file(use_cached=True, spoiler=True)
        files.append(file)

    ping = "Sent by <@" + str(ctx.author.id) + ">\n";
    if text != "":
        ping = ping + "**" + text + "**"
    await ctx.send(content=ping, files=files)
    await ctx.message.delete()


@client.command(pass_context=True,brief="Vriska.")
async def vriska(ctx):
    await ctx.send("<:vriska:776019724956860417>")
    await ctx.message.delete()

@client.command(pass_context=True,brief="Sends trigger document in simple text form.")
@commands.check_any(checks.is_in_skys(), checks.is_in_DMs())
async def triggerList(ctx):
    if checks.is_in_skys() or not checks.is_in_guild():
        url = "https://docs.google.com/document/d/1RHneHjg6oKlenY7j-jk_sp5ezkxglpRsNoZuoUeM6Jc/export?format=txt"
        
        content = requests.get(url)

        text = re.sub(r'(\r\n){3,}','\n\n', content.text)
        text = formatTriggerDoc(text)

        with open("html.txt", "w", encoding="utf-8") as f:
            f.write(text)
        
        output = splitLongMsg(text)

        for o in output:
            await ctx.send(o)


@client.command(pass_context=True,brief="Sends list of HussieBot's currently blacklisted phrases.")
async def hussieBlacklist(ctx):
    output = "Currently Blacklisted Phrases: \n"
    for phrase in bannedPhrases:
        output += phrase + "\n"

    output = output.rstrip("\n")
    await ctx.send(output)


@client.command(pass_context=True,brief="Sends a number of whitespace lines to clear a channel.", help="Use 'permanent' or a specified number of hours for auto-deletion.")
@commands.cooldown(1, 300, commands.BucketType.user)
async def whitespace(ctx,delete_after):
    try:
        int(delete_after)
    except ValueError:
        if delete_after[0] in ["p", "s"]:
            delete_after = -1
        else:
            delete_after = 8
        
    output = "```"
    output += (' '.join(random.choices(starsList + spaces, k=900)))

    hours = None if delete_after == -1 else int(delete_after) * 3600
    await ctx.send(output + "```",delete_after=hours)

@client.command(pass_context=True,brief="Sends bubblewrap message.")
async def bubblewrap(ctx,size="5x5"):
    dimensions = re.split('x| ',size)
    try:
        width = int(dimensions[0])
        height = int(dimensions[1])
    except:
        raise checks.InvalidArgument("Invalid size! Run hbs;bubblewrap for a 5x5 grid, or specify a grid size like this: hbs;bubblewrap 9x9")
    output = "Bubble Wrap!\n\n" + (("||pop||" * width + "\n") * height)
    output = output.rstrip("\n")
    if len(output) > 2000:
        await ctx.send("Unfortunately discord's message character limit doesn't support bubble wrap that size :( \nHere's what I could fit!") 
        outputArr = splitLongMsg(output, 2000)
        output = outputArr[0]
    await ctx.send(output)
    
@client.event
async def on_error(event_name, *args):
    try:
        if (event_name == "on_raw_reaction_add") and (sys.exc_info()[1].code == 10008):
            return #IGNORE ERRORS IN RAW_REACTION_ADD WHEN A MESSAGE IS REACTED TO AND THEN DELETED
    except:
        pass
    
    f = io.StringIO()
    with redirect_stderr(f):
        logging.exception("Exception from event {}".format(event_name))
    out = f.getvalue()

    await client.get_user(VRISKA_ID).send(str(out))

if __name__ == "__main__":
    loaded = []
    failed = []
    failedExc = []
    for extension in startup_extensions:
        try:
            client.load_extension("cogs." + extension)
            loaded.append(extension)
            
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            failed.append(extension)
            failedExc.append(exc)

    loadOutput = "Loaded Extensions: "
    failOutput = "Failed Extensions: \n"
    if len(loaded) >= 1:
        for i in range(0,len(loaded)-1):
            loadOutput += loaded[i] + ", "
        loadOutput += loaded[len(loaded)-1] + "\n"
        sys.stdout.write(loadOutput)

    if len(failed) >= 1:
        sys.stdout.write(failOutput)
        for i in range(0,len(failed)):
            sys.stdout.write(f'\t{failed[i]}, Exception: {failedExc[i]}\n')


    sys.stdout.flush()

client.run(os.environ["token"])

