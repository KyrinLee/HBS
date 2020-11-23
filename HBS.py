import discord
import logging
import re
import json
import asyncio

from discord.ext import commands

import time
from datetime import datetime, date, timedelta

import os
import pk

import sys

import psycopg2
from psycopg2 import Error

import checks

from HelpMenu import HBSHelpCommand

from functions import splitLongMsg, formatTriggerDoc
import requests


startup_extensions = ["Counters","Yeets","CommandErrorHandler","Starboards","DumbCommands","EmojiTracking","AdminCommands"]

DATABASE_URL = os.environ['DATABASE_URL']
pluralkit_id = 466378653216014359
hussiebot_id = 480855402289037312
toddbot_id = 461265486655520788

week = timedelta(days=7)
month = timedelta(days=30)

bannedPhrases = ["Good Morning", "Good Mornin", "Good Evening", "Good Evenin", "Fair Enough", "Cool Thanks", "Mornin Fellas", "Evenin Fellas"]

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(
    command_prefix=("hbs;","\hbs;","hbs ","\hbs ","Hbs;","\Hbs;","Hbs ","\Hbs "),
    owner_ids=[707112913722277899,259774152867577856,279738154662232074],
    case_insensitive=True,
    help_command=HBSHelpCommand(indent=4,paginator=commands.Paginator()),
    description="HussieBot Oppression & More",
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
    if message.guild is not None:
        
    #HANDLE HUSSIEBOT VRISKA REACTS
        if message.author.id == hussiebot_id: #if hussiebot
                    if (message.content == "<:vriska:480855644388458497>" or message.content == ":vriska:" or message.content == ":eye:"): 
                            await message.delete()
                    for phrase in bannedPhrases:
                        if message.content.find(phrase) != -1:
                            await message.delete()
                            #break

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
            
    await client.process_commands(message)
                        
    
@client.event
async def on_raw_reaction_add(payload):
    #HANDLE PK DELETION
    if payload.emoji.name == "❌":
        #GET CHANNEL AND MESSAGE
        channel = client.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        
        #REMOVE HUSSIE MESSAGES + TODD MESSAGES
        if (msg.author.id == hussiebot_id or msg.author.id == toddbot_id):
            if msg.author.id == hussiebot_id:
                with open('hussieDeleted.txt', 'a') as f:
                    f.write(msg.content + "\n")
            await msg.delete()

        #REMOVE SPOILERED IMAGES FROM HBS
        if msg.author.id == client.user.id and len(msg.mentions) > 0 and msg.mentions[0].id == payload.user_id:
            await msg.delete()
        
        #REMOVE PK MESSAGES
        if payload.user_id != pluralkit_id:
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
    
@client.event
async def on_error(event_name, *args):
    log = logging.exception("Exception from event {}".format(event_name))
    await client.get_user(707112913722277899).send(log)

if __name__ == "__main__":
    loaded = []
    failed = []
    failedExc = []
    for extension in startup_extensions:
        try:
            client.load_extension(extension)
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

