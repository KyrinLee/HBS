import discord
from discord.ext import commands
import time
from datetime import datetime, date

import sys

import os
import psycopg2

from psycopg2 import Error

import checks

DATABASE_URL = os.environ['DATABASE_URL']

from string import Formatter
from datetime import timedelta

def strfdelta(tdelta, fmt='{D:02}d {H:02}h {M:02}m {S:02}s', inputtype='timedelta'):
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

class dayCount(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def reset(self,ctx: commands.Context, *, counter=None):

        if counter==None:
            raise checks.InvalidArgument(message="Please include counter name.")
        
        connection = psycopg2.connect(DATABASE_URL, sslmode='require')

        cursor = connection.cursor()

        currTime = datetime.fromtimestamp(time.time())

        cursor.execute("CREATE TABLE IF NOT EXISTS counters (name VARCHAR(255) UNIQUE, timestamp TIMESTAMP, mentions INT)")

        '''
        try:
            cursor.execute("INSERT INTO counters (name, timestamp, mentions) VALUES (%s, %s, %s)",(counter,currTime,0))
            await ctx.send("Counter " + counter + " created.")
        '''

        cursor.execute("SELECT * FROM counters")
        data = cursor.fetchall()

        keywords = [w[0] for w in data[0]]

        await ctx.send(str(keywords))

        '''
        cursor.execute("SELECT * FROM counters WHERE name=%s",(counter,))
        data = cursor.fetchall()

        keywords = data[0][0]

        mentions = data[0][2] + 1
        timeStamp = data[0][1]
        
        cursor.execute("UPDATE counters SET timestamp=%s, mentions=%s WHERE name=%s",(currTime,mentions,counter))

        timeDiff = currTime - timeStamp

        output = "Counter " + counter + " updated - it has been " + strfdelta(timeDiff) + " since this counter was last reset. This counter has been reset " + str(mentions) + " time"
        if mentions == 1:
            output += "."
        else:
            output += "s."
            
        await ctx.send(output)
        '''

        connection.commit()
        cursor.close()
        connection.close()

        
    @commands.command()
    async def newCounter(self,ctx: commands.Context, counter=None):

        if counter == None:
            raise checks.InvalidArgument("Please include counter name.")
        else:
            await ctx.send("Vriska hasn't coded the checky thing yet. Ping her bc she forgot.")

def setup(client):
    client.add_cog(dayCount(client))
