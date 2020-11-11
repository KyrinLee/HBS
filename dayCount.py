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

        cursor.execute("CREATE TABLE IF NOT EXISTS counters (name VARCHAR(255) UNIQUE, timestamp TIMESTAMP, mentions INT)") #SAFEGUARD, SHOULDN'T BE NEEDED

        cursor.execute("SELECT * FROM counters")
        data = cursor.fetchall()

        keywords = [w[0] for w in data]

        words = [w for w in keywords if (counter.find(w)!= -1)]

        if len(words) >= 1:
            word = words[0].lower()
            
            cursor.execute("SELECT * FROM counters WHERE name=%s",(word,))
            data = cursor.fetchall()

            mentions = data[0][2] + 1
            timeStamp = data[0][1]
            
            cursor.execute("UPDATE counters SET timestamp=%s, mentions=%s WHERE name=%s",(currTime,mentions,word))

            timeDiff = currTime - timeStamp

            output = "Counter " + word + " updated - it has been " + strfdelta(timeDiff) + " since this counter was last reset. This counter has been reset " + str(mentions) + " time"
            if mentions == 1:
                output += "."
            else:
                output += "s."
                
            await ctx.send(output)

        else:
            raise checks.InvalidArgument("Counter not found.")
        

        connection.commit()
        cursor.close()
        connection.close()

        
    @commands.command(aliases=['addCounter'])
    async def newCounter(self,ctx: commands.Context, counter=None):

        if counter == None:
            raise checks.InvalidArgument("Please include counter name.")
        else:
            counter = counter.lower()
            result = await checks.confirmationMenu(self.client, ctx, f'Would you like to create new counter {counter}?')
            if result == 1:
                try:
                    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                    cursor = conn.cursor()
                    currTime = datetime.fromtimestamp(time.time())

                    cursor.execute("INSERT INTO counters (name, timestamp, mentions) VALUES (%s, %s, %s)",(counter,currTime,0))
                    await ctx.send(f'Counter {counter} created.')
                except:
                    raise checks.FuckyError()
                finally:
                    conn.commit()
                    cursor.close()
                    conn.close()
                
            elif result == 0:
                await ctx.send("Counter creation cancelled.")
            else:
                await ctx.send("Something be fucky here. Idk what happened. Maybe try again?")

    @commands.is_owner()
    @commands.command(aliases=['removeCounter'])
    async def deleteCounter(self,ctx: commands.Context, counter=None):
        await ctx.send("nope. o(-<")

    @commands.command(aliases=['counters','listCounters','allCounters','viewCounters'])
    async def returnCounters(self, ctx:commands.Context):
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM counters")
        counters = cursor.fetchall()

        await ctx.send(str([row[0] for row in counters]))
        await ctx.send(str([row[2] for row in counters]))

        maxName = len(str(max([row[0] for row in counters])))
        maxNum = len(str(max([row[2] for row in counters])))

        output = "`"

        for i in range(0,len(counters)):
            output += f'{counters[i][0].rjust(maxName)}: {str(counters[i][2]).rjust(maxNum)} resets, last reset: {counters[i][1]}\n'

        output += "`"

        await ctx.send(output)

        conn.commit()
        cursor.close()
        conn.close()
        
def setup(client):
    client.add_cog(dayCount(client))
