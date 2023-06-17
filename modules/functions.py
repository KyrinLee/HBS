import re
import sys
from modules import checks

import discord
from discord.ext import commands

from resources.constants import *

from datetime import datetime, date

import aiohttp
import asyncio

from pytz import timezone
import pytz

import psycopg2

def get_today():
    return datetime.now(tz=pytz.utc).astimezone(timezone('US/Pacific')).replace(hour=0,minute=0,second=0,microsecond=0)

def database_connect(database=0):
    conn = psycopg2.connect(
        host=HOST,
        database=DATABASE_1_NAME,
        user=USER,
        password=PASSWORD)
    cursor = conn.cursor()
    return conn, cursor

def database_disconnect(conn, cursor):
    conn.commit()
    cursor.close()
    conn.close()

async def run_query(query, values=(), database=0):
    async with databaseSem:
        conn, cursor = database_connect(database)
        cursor.execute(query, values)
        try:
            data = cursor.fetchall()
        except psycopg2.ProgrammingError as e:
            if str(e) == "no results to fetch":
                data = []
            else:
                raise

        database_disconnect(conn, cursor)

    return data

def nsyl(word):
  try:
      return [len(list(y for y in x if y[-1].isdigit())) for x in dictionary[word.lower()]] 
  except:
      return [-1]

async def check_for_react(msg, reaction_name, user_id):
  reacts = msg.reactions
  for r in reacts:
      if (isinstance(r.emoji, str) and r.emoji == reaction_name) or (isinstance(r.emoji, (discord.Emoji, discord.PartialEmoji)) and r.emoji.name == reaction_name):
          users = await r.users().flatten()
          for u in users:
              if u.id == user_id:
                  return True
  return False

async def split_and_send(txt, channel):
    output = split_string(txt, 2000)
    for o in output:
        await channel.send(o)

def split_string(str, limit, sep=" "):
    words = str.split(' ')
    if max(map(len, words)) > limit:
        raise ValueError("limit is too small")
    res, part, others = [], words[0], words[1:]
    for word in others:
        if len(sep)+len(word) > limit-len(part):
            res.append(part)
            part = word
        else:
            part += sep+word
    if part:
        res.append(part)
    return res
    
def escapeCharacters(txt):
    if txt:
        txt = re.sub("\*","\\\*",txt)
        txt = re.sub("\|","\\\|",txt)
        txt = re.sub("\_","\\\_",txt)
    return txt

def formatTriggerDoc(txt):
    txtArr = re.split('(censor the text as well.)',txt)

    txtArr[2] = re.sub(r'\[([\s\S]*?)\]',r'||\1||',txtArr[2])
    txtArr[2] = re.sub(r'(\*\*[\s\S]*?\*\*)',r'__\1__',txtArr[2])
    txtArr[2] = re.sub(r'-        ',r'      - ',txtArr[2])
    txtArr[2] = re.sub(r'\r\n\|\|',r'||\n',txtArr[2])

    return "".join(txtArr)


# ----- CONFIRMATION MENU ----- #

async def confirmationMenu(client, ctx, confirmationMessage="",autoclear=""):
    msg = await ctx.send(confirmationMessage)
  
    await msg.add_reaction(check_emoji)
    await msg.add_reaction(x_emoji)

    def check(reaction, user):
        return user == ctx.author

    try:
        reaction, user = await client.wait_for('reaction_add', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        if autoclear: await msg.delete()
        raise checks.OtherError("Operation timed out.")

    if user == ctx.author:
        if str(reaction) == x_emoji:
            if autoclear: await msg.delete()
            raise checks.OtherError("Operation cancelled.")
        elif str(reaction) == check_emoji:
            if autoclear: await msg.delete()
            return 1
    else:
        if autoclear: await msg.delete()
        raise checks.FuckyError()

# ----- FIND MESSAGE VIA ID OR LINK ----- #
async def getMessage(client, ctx,id=None, channelId=None):
    async with ctx.channel.typing():
        if id == None:
            raise TypeError("Please include valid message ID or link.")

        elif str(id)[0:4] == "http":
            link = id.split('/')
            channel_id = int(link[6])
            msg_id = int(link[5])
            msg = await client.get_channel(channel_id).fetch_message(msg_id)
        else:
            msg = []
            for channel in ctx.guild.text_channels:
                try:
                    msg.append(await channel.fetch_message(id))
                except:
                    continue
        
            if msg == []:
                await awaitMsg.delete()
                raise TypeError("That message does not exist.")
            elif len(msg) > 1:

                await awaitMsg.delete()
                raise TypeError("Multiple messages with that ID found. Please run the command again using the message link instead of the ID.")
        
    return msg[0]

def numberFormat(num):
    numAbbrs = ["k","m","b","t"]
    count = 0
    
    if num < 100000:
        return num
      
    power = 0
    while num >= 1:
        num = num / 10
        power = power + 1
    num = round(num, 3)
    sys.stdout.write(str(num) + "\n")
    
    while True:
        num = num * 10
        power = power - 1
        if power % 3 == 0:
            break
          
    sys.stdout.write(str(num) + "\n")

    power = power // 3 - 1
    if len(str(num)) > 5:
        num = str(num)[0:4]

    num_string = str(num)
    
    if '.' not in num_string:
      num_string = num_string + "."

    output = num_string + "0000"
    return output[0:4].rstrip('.') + numAbbrs[power]
    
    #return re.sub('\.0+$','',str(num)) + numAbbrs[power]


import time
from datetime import datetime, date, timedelta
from string import Formatter

def strfdelta(tdelta, fmt='{D}d {H}h {M}m {S:02}s', inputtype='timedelta'):
    """Convert a datetime.timedelta object or a regular number to a custom-
    formatted string, just like the stftime() method does for datetime.datetime
    objects.

    The fmt argument allows custom formatting to be specified.  Fields can 
    include seconds, minutes, hours, days, and weeks.  Each field is optional.

    Some examples:
        '{D:02}d {H:02}h {M:02}m {S:02}s' --> '05d 08h 04m 02s' (default)
        '{W}w {D}d {H}:{M:02}:{S:02}'     --> '4w 5d 8:04:02'
        '{D:2}d {H:2}:{M:02}:{S:02}'      --> ' 5d  8:04:02'
        '{H}h {S}s'                       --> '72h 800s'

    The inputtype argument allows tdelta to be a regular number instead of the  
    default, which is a datetime.timedelta object.  Valid inputtype strings: 
        's', 'seconds', 
        'm', 'minutes', 
        'h', 'hours', 
        'd', 'days', 
        'w', 'weeks'
    """

    # Convert tdelta to integer seconds.
    if inputtype == 'timedelta':
        remainder = int(tdelta.total_seconds())
    elif inputtype in ['s', 'seconds']:
        remainder = int(tdelta)
    elif inputtype in ['m', 'minutes']:
        remainder = int(tdelta)*60
    elif inputtype in ['h', 'hours']:
        remainder = int(tdelta)*3600
    elif inputtype in ['d', 'days']:
        remainder = int(tdelta)*86400
    elif inputtype in ['w', 'weeks']:
        remainder = int(tdelta)*604800

    f = Formatter()
    desired_fields = [field_tuple[1] for field_tuple in f.parse(fmt)]
    possible_fields = ('W', 'D', 'H', 'M', 'S')
    constants = {'W': 604800, 'D': 86400, 'H': 3600, 'M': 60, 'S': 1}
    values = {}
    for field in possible_fields:
        if field in desired_fields and field in constants:
            values[field], remainder = divmod(remainder, constants[field])
    return f.format(fmt, **values)

def line_count():
    """import glob
    line_count = 0
    char_count = 0
    for file_path in glob.glob("./**/*.py",recursive=True):
        try:
            with open(file_path) as file:
                line_count += len(file.readlines())
        except:
            pass"""
    
    # broken
    # use dir -Recurse *.py | Get-Content | Measure-Object -Line in powershell

    return 2814
