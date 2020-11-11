import discord
import logging
import re
import json
import asyncio

from discord.ext import commands

import time
from datetime import datetime, date

import os
import pk

import sys

import psycopg2
from psycopg2 import Error

import checks
import functions

startup_extensions = ["dayCount","Yeets","CommandErrorHandler","Starboards","DumbCommands","EmojiTracking","AdminCommands"]

DATABASE_URL = os.environ['DATABASE_URL']

intents = discord.Intents.default()
intents.members = True

client = commands.Bot(
    command_prefix=("hbs;","\hbs;","hbs ","\hbs"),
    owner_ids=[707112913722277899,259774152867577856],
    case_insensitive=True,
    help_command=None,
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

    if message.server is not None:

#HANDLE HUSSIEBOT VRISKA REACTS
        bannedPhrases = ["Good Morning is a valid kid name.", "Fair Enough is a valid kid name.",
                         "Cool Thanks is a valid kid name."]
        if message.author.id == 480855402289037312: #if hussiebot
                    if (message.content == "<:vriska:480855644388458497>" or message.content == ":vriska:" or message.content == ":eye:"): 
                            await message.delete()
                    if message.content in bannedPhrases:
                            await message.delete()

    else:
        raise commands.NoPrivateMessage()

    
    await client.process_commands(message)
                        
    

@client.event
async def on_raw_reaction_add(payload):
    #HANDLE PK DELETION
    if payload.emoji.name == "❌":
        result = -1
        channel = client.get_channel(payload.channel_id)
        msg = await channel.fetch_message(payload.message_id)
        sys = await pk.get_pk_system_from_userid(payload.user_id)
        if sys != None:
            
            sys = sys["id"]

            isMenu = False

            reacts = msg.reactions
            for react in reacts:
                if react.emoji == "✅":
                    users = await react.users().flatten()
                    for user in users:
                        if user.id == 466378653216014359:
                            isMenu = True

            if msg.author.id == 466378653216014359 and (not isMenu):
                for embed in msg.embeds:
                    emb = json.dumps(embed.to_dict())
                    if (emb.find(sys) != -1):
                        result = 1
                if result == 1:
                    await msg.edit(suppress=True)
                    await msg.clear_reactions()
                    msgDel = client.get_emoji(767960168444723210)
                    await msg.add_reaction(msgDel)

        if msg.author.id == 753345733377261650 and  len(msg.mentions) > 0 and msg.mentions[0].id == payload.user_id:
            await msg.delete()
        #await channel.send("message deleted")

    #REMOVE HUSSIE MESSAGES 
    if payload.emoji.name == "❌" and msg.author.id == 480855402289037312:
        await msg.delete()


@client.command(pass_context=True)
async def spoil(ctx, *, text="", description="Resends image(s) under spoiler tags. Can send up to 10 images."):
    
    files = []
    for a in ctx.message.attachments:
        file = await a.to_file(use_cached=True, spoiler=True)
        files.append(file)

    ping = "Sent by <@" + str(ctx.author.id) + ">\n";
    if text != "":
        ping = ping + "**" + text + "**"
    await ctx.send(content=ping, files=files)
    await ctx.message.delete()


@client.command(pass_context=True)
async def help(ctx, command=None):
    embed = discord.Embed(title="HBS Help", description="HussieBot Oppression & More", color=0x005682)

    embed.set_thumbnail(url="https://media.discordapp.net/attachments/753349219808444438/770918408371306516/hbs.png")
    embed.add_field(name="Reset Counter", value="**hbs;reset <countername>**\nResets given counter.\n", inline=False)
    embed.add_field(name="Get Emoji Usage", value="**hbs;getEmojiUsage [num] [-s | -a] **\nReturns top and bottom [num] emojis (default 15). Static or animated emojis can be specified using -s or -a.\n", inline=False)
    embed.add_field(name="Get Full Emoji Usage", value="**hbs;getFullEmojiUsage**\nReturns all emojis in server with usage stats, sorted by most to least used.\n", inline=False)
    embed.add_field(name="Spoil Images", value="**hbs;spoil [text] <image(s)>\n\hbs;spoil [text] <image(s)> (to escape pk autoproxy.)**\nResends image(s) under spoiler tag, with text. Can spoil up to 10 images at once.\n",inline=False)
    embed.set_footer(text="HBS is maintained by Vriska & Rose @ramblingArachnid#8781.")
    await ctx.send(embed=embed)

@client.command(pass_context=True)
async def vriska(ctx):
    await ctx.send("<:vriska:480855644388458497>")
    await ctx.message.delete()
    
@client.event
async def on_error(event_name, *args):
    logging.exception("Exception from event {}".format(event_name))


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
    if len(loaded) > 1:
        for i in range(0,len(loaded)-1):
            loadOutput += loaded[i] + ", "
        loadOutput += loaded[len(loaded)-1] + "\n"
        sys.stdout.write(loadOutput)

    if len(failed) > 1:
        sys.stdout.write(failOutput)
        for i in range(0,len(failed)):
            sys.stdout.write(f'\t{failed[i]}, Exception: {failedExc[i]}\n')

client.run(os.environ["token"])

