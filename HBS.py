import discord
import logging
import re
import json
import asyncio

from discord.ext import commands

import time
from datetime import datetime, date, timedelta
import string

import os
import sys

import psycopg2
from psycopg2 import Error
import random

import requests
import io
from contextlib import redirect_stderr

import random
import syllables

from modules import checks, pk, pluralKit
from modules.HelpMenu import HBSHelpCommand
from modules.functions import *
from resources.constants import *

intents = discord.Intents.default()
intents.members = True
intents.presences = True

startup_extensions = ["Counters","Yeets","CommandErrorHandler","Starboards","DumbCommands","EmojiTracking","AdminCommands","Birthdays","Reminders"]

blacklisted_channels = {}
reaction_timeouts = {}

client = commands.Bot(
    command_prefix=("hbs;","\hbs;","Hbs;","\Hbs;","hbs ","Hbs ","\hbs ","\Hbs "),
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
        sys.stdout.write(str(g.name) + ", Owner ID: " + str(g.owner_id) + "\n");

    sys.stdout.flush()

    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vars WHERE name = 'game'")
    game = cursor.fetchall()[0][1]
    await client.change_presence(activity=discord.Game(name=game))

    
    client.get_cog('Birthdays').time_check.start()
    client.get_cog('Birthdays').update_cache.start()

    conn.commit()
    cursor.close()
    conn.close()


@client.before_invoke
async def common(ctx):
    await ctx.message.clear_reactions()

async def timeout_reaction_check(reaction_name, time=10):
    result = False

    try:
        start_time = reaction_timeouts.get(reaction_name)[0]
        expire_time = reaction_timeouts.get(reaction_name)[1]
            
        if expire_time > datetime.utcnow() and (datetime.utcnow() - start_time).seconds > 4:
            return False
            
    except:
        pass
    
    wait_time = timedelta(minutes=time)
    
    expire_time = datetime.utcnow()+wait_time
    start_time = datetime.utcnow()

    reaction_timeouts.update({reaction_name: [start_time,expire_time]})

    return True

@client.event
async def on_message(message: discord.Message):
    if (message.guild == None):
        await client.process_commands(message)
        return
        
    #HANDLE HUSSIEBOT VRISKA REACTS
    if message.author.id == HUSSIEBOT_ID: #if hussiebot
        if (message.content in ["<:vriska:480855644388458497>",":vriska:",":eye:"]): 
            await message.delete()
        if message.content == "Andrew Hussie is a valid troll name.":
            await message.delete()
            await message.channel.send("Andrew Hussie is a valid troll. And my boyfriend! " + blobspade)
        for phrase in bannedPhrases:
            if message.content.find(phrase) != -1:
                await message.delete()
                break

    try:
        #IF NOT IN VENT, AUTHOR NOT HBS, AND NOT COMMAND
        if message.channel.category_id != VENT_CATEGORY_ID and message.author.id != client.user.id and not any(message.content.startswith(s) for s in client.command_prefix):
            message_content = message.clean_content.strip().lower()

            expire_time = blacklisted_channels.get(message.channel.id)
            if expire_time == None or expire_time < datetime.utcnow():
                if expire_time != None: blacklisted_channels.pop(message.channel.id)

                if message_content.find('vriska') != -1 or str(message.guild.get_member(HUSSIEBOT_ID).status) == "offline":             
                    if message.webhook_id == None and not message_content.startswith("pk;") and not any(phrase.lower() in message_content for phrase in bannedPhrases):
                        #VRISKA SERKET
                        if (message_content == "vriska serket"):
                            await asyncio.sleep(1)
                            await message.channel.send("Vriska Serket is a valid troll ::::)")
                        #ANDREW HUSSIE
                        if (message_content == "andrew hussie"):
                            await asyncio.sleep(1)
                            await message.channel.send("Andrew Hussie is a valid troll. And my boyfriend! " + blobspade)
                        #VALID KID NAME
                        elif (bool(re.match("\S{4}\s(\S){6,7}$",message_content))):
                            await asyncio.sleep(1)
                            await message.channel.send(f'{string.capwords(message_content)} is a valid kid name.')
                        #VALID TROLL NAME
                        elif (bool(re.match("\S{6}\s(\S){6}$",message_content))):
                            await asyncio.sleep(1)
                            await message.channel.send(f'{string.capwords(message_content)} is a valid troll name.')

                elif message.webhook_id == None:
                    #VALID ANCESTOR
                    if (bool(re.match("(?:the|\S{8})\s(\S){8}$",message_content))):
                        await asyncio.sleep(1)
                        await message.channel.send(f'{string.capwords(message_content)} is a valid ancestor name.')

                    #VALID CLASSPECT
                    match = re.match("(\w+) of (\w+)$", message_content)
                    if match:
                        first_word_is_one_syllable = nsyl(match.group(1))[0] == 1 or syllables.estimate(match.group(1)) == 1
                        second_word_is_one_syllable = nsyl(match.group(2))[0] == 1 or syllables.estimate(match.group(2)) == 1
                        if (first_word_is_one_syllable and second_word_is_one_syllable):
                            await asyncio.sleep(1)
                            await message.channel.send(f'{match.group(1).capitalize()} of {match.group(2).capitalize()} is a valid classpect.')

                #HUSSIE
                if any(i in message_content for i in ["hussie"]):
                    if message_content.count("hussie") > message_content.count("suppressor") and message_content.count("hussie") > message_content.count("oppressor"):
                        if message.channel.id == HBS_CHANNEL_ID or await timeout_reaction_check("hussie"):
                            await message.add_reaction(blobspade)
                #COWARDBOT
                if any(i in message_content for i in ["cowardbot"]):
                    if message.channel.id == HBS_CHANNEL_ID or await timeout_reaction_check("hussie"):
                        await message.add_reaction(blobspade)
                       
                #SPAGHETTI    
                if any(i in message_content for i in ["spag","spah"]):  #message.channel.id != FOOD_CHANNEL_ID to ban from food 
                    if message.channel.id == HBS_CHANNEL_ID or await timeout_reaction_check("spaghetti"):
                        await message.add_reaction(spaghetti)
                #HBS
                if any(i in message_content for i in ["hbs", "hussiebotsuppressor", "hussiebotoppressor"]):
                    if message_content == "hbs":
                        await message.channel.send("owo?")
                    else:
                        if message.channel.id != HBS_CHANNEL_ID: #and await timeout_reaction_check("hbs")
                            await message.add_reaction(looking)
                        num = random.random()
                        if num < .1:
                            await message.channel.send(random.choice(["owo","owo?","uwu","OwO"]))
                       
                #HOMESTUCK
                if message.channel.id != HOMESTUCK_CHANNEL_ID and message.author.id != PLURALKIT_ID and any(i in message_content for i in ["homestuck"]):
                    if message.channel.id == HBS_CHANNEL_ID or await timeout_reaction_check("homestuck"):
                        await message.add_reaction(looking)
    except:
        raise
    
    if (message.author.id != client.user.id) and (message.guild.id == SKYS_SERVER_ID) and (message.webhook_id == None):
        await client.get_cog('EmojiTracking').on_message_emojis(message)
            
    await client.process_commands(message)                 

@client.event
async def on_raw_reaction_add(payload):
    if (payload.guild_id == None):
        return

    #HANDLE DELETION
    if payload.emoji.name == x:
        #GET CHANNEL AND MESSAGE
        channel = client.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)

        #REMOVE UNWANTED MESSAGES FROM BOTS
        if (msg.author.id in [HUSSIEBOT_ID, TODDBOT_ID]):
            await msg.delete()

        #YAG AND TUPPERBOX DELETION, IF NOT MENU
        if (msg.author.id in [YAGBOT_ID, TUPPERBOX_ID]):
            if not await check_for_react(msg, x, msg.author.id):
                await msg.delete()

        #PLURALKIT DELETION
        if (msg.author.id == PLURALKIT_ID):
            system = await pk.get_system_by_discord_id(payload.user_id)
            system_id = system.hid
            message_text = ""
            for e in msg.embeds:
                message_text = message_text + str(e.to_dict())
            if system_id in message_text:
                await msg.delete()

        #HBS DELETION
        if (msg.author.id == client.user.id) and (payload.user_id != client.user.id):
            await msg.delete()

    if payload.emoji.name == "hussiebap" or payload.emoji.name == newspaper2:
        #GET CHANNEL AND MESSAGE
        channel = client.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)

        reacts = msg.reactions
        count = 0
        for r in reacts:
            if str(r.emoji) in ["<:hussiebap:754482819513712721>", newspaper2]:
                count += r.count      
        
        if msg.author.id == HUSSIEBOT_ID and msg.channel.category_id != VENT_CATEGORY_ID and count == 1:
            await channel.send("Hey! Don't bap my boyfriend! " + str(blobspade))

@client.event
async def on_member_join(member):
    if member.guild.id == SKYS_SERVER_ID:
        if member.id == VRISKA_ID:
            spidermod_role = member.guild.get_role(SPIDERMOD_ROLE_ID)
            await member.add_roles(spidermod_role)

@client.event
async def on_member_update(before, after):
    if before.guild.id ==SKYS_SERVER_ID:
        if before.id == HUSSIEBOT_ID:
            if str(before.status) == "online" and str(after.status) == "offline":
                hussie_phrase = random.choice(["The one and only Andrew", "My boyfriend", "My precious kismesis", "My love", "My fiance", "My matesprit", "Dumb bitch", "Goddamn coward", "Goddamn little fruit"])
                await client.get_channel(HBS_CHANNEL_ID).send(hussie_phrase + " Hussie just went offline. :pensive:")

@client.command(pass_context=True,brief="Spoil an image.", aliases=['spoiler'])
async def spoil(ctx, *, text=""):
    
    files = []
    for a in ctx.message.attachments:
        file = await a.to_file(use_cached=True, spoiler=True)
        files.append(file)
    
    await ctx.message.delete()

    ping = "Sent by <@" + str(ctx.author.id) + ">\n";
    if text != "":
        ping = ping + "**" + text + "**"
    await ctx.send(content=ping, files=files)

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

@client.command(pass_context=True, aliases=["mute"], brief="Tells HBS to shut up in a certain channel for a while.")
async def shutup(ctx, time="1h"):
    hours = 0
    minutes = 0
    seconds = 0
    
    time_list = re.findall("\d+[h|m|s]",time)
    for time in time_list:
        time_num = re.findall("\d+", time)[0]
        time_letter = re.findall("[h|m|s]",time)[0]
        if time_letter == "h":
            hours += int(time_num)
        elif time_letter == "m":
            minutes += int(time_num)
        elif time_letter == "s":
            seconds += int(time_num)

    wait_time = timedelta(hours=hours, minutes=minutes,seconds=seconds)
    expire_time = datetime.utcnow()+wait_time

    blacklisted_channels.update({ctx.channel.id: expire_time})
    await ctx.channel.send(f'HBS successfully muted in this channel for {strfdelta(wait_time, fmt="{H}h{M}m{S}s").replace("0h","").replace("0m","").replace("0s","")}.')

@client.command(pass_context=True)
@checks.is_vriska()
async def getvar(ctx, varname):
    var = globals()[varname]
    await ctx.channel.send(str(var))

@client.event
async def on_error(event_name, *args):
    try:
        if (event_name in ["on_raw_reaction_add","on_message"]) and (sys.exc_info()[1].code == 10008):
            return #IGNORE ERRORS IN RAW_REACTION_ADD WHEN A MESSAGE IS REACTED TO AND THEN DELETED
    except:
        pass
    
    '''f = io.StringIO()
    with redirect_stderr(f):
        logging.exception("Exception from event {}".format(event_name))
    out = f.getvalue()

    await client.get_user(VRISKA_ID).send(str(out))'''
    logging.exception("Exception from event {}".format(event_name))

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
    conn.close()'''
