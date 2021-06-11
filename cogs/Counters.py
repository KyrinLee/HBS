import discord
from discord.ext import commands
import time
from datetime import datetime, date, timedelta

import sys

import os
import psycopg2

from modules.checks import FuckyError
from modules import checks
from modules.functions import *
from discord import InvalidArgument

import asyncio
resetSem = asyncio.Semaphore(1)

DATABASE_URL = os.environ['DATABASE_URL']

class Counters(commands.Cog, name="Counter Commands"):
    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        if not ctx.guild.id == SKYS_SERVER_ID:
            raise checks.WrongServer()
        return True

    @commands.command(aliases=['reset','update'],brief="Reset/Update a counter.")
    async def resetCounter(self,ctx: commands.Context, *, counter=None):
        async with resetSem:
            if counter==None:
                raise InvalidArgument("I can't reset a counter if you don't tell me which one! <:angercry:757731437326762014>")
            
            conn, cursor = database_connect()
            currTime = datetime.utcnow()

            cursor.execute("CREATE TABLE IF NOT EXISTS counters (name VARCHAR(255) UNIQUE, timestamp TIMESTAMP, mentions INT)") #SAFEGUARD, SHOULDN'T BE NEEDED

            #FIND KEYWORDS
            cursor.execute("SELECT * FROM counters")
            data = cursor.fetchall()

            keywords = [w[0] for w in data]

            words = [w for w in keywords if (counter.find(w)!= -1)]

            if len(words) >= 1:
                word = max(words, key = len).lower()
                
                cursor.execute("SELECT * FROM counters WHERE name=%s",(word,))
                data = cursor.fetchall()

                mentions = data[0][2] + 1
                timeStamp = data[0][1]

                timeDiff = currTime - timeStamp

                if timeDiff < timedelta(minutes=1):
                    await ctx.send("This timer is on cooldown! Please wait " + strfdelta((timedelta(minutes=1) - timeDiff),fmt='{S:02}s') + " to reset again.")
                else:
                    cursor.execute("UPDATE counters SET timestamp=%s, mentions=%s WHERE name=%s",(currTime,mentions,word))

                    output = "Counter " + word + " updated - it has been " + strfdelta(timeDiff) + " since this counter was last reset. This counter has been reset " + str(mentions) + " time"
                    if mentions == 1:
                        output += "."
                    else:
                        output += "s."
                        
                    await ctx.send(output)

            else:
                raise InvalidArgument("That's not a real counter! <:angercry:757731437326762014>")

            database_disconnect(conn, cursor)

    @commands.command(aliases=['addCounter'],brief="Create a new counter.")
    async def newCounter(self,ctx: commands.Context, counter=None):

        if counter == None:
            raise InvalidArgument("You gotta name the counter! <:angercry:757731437326762014>")

        else:
            counter = counter.lower()
            #SEARCH DATABASE TO SEE IF COUNTER ALREADY EXISTS
            conn, cursor = database_connect()

            cursor.execute("SELECT * FROM counters WHERE name = %s",(counter,))
            counters = cursor.fetchall()

            #IF COUNTER DOESN'T EXIST, CREATE IT
            if len(counters) == 0:
                if await confirmationMenu(self.client, ctx, f'Would you like to create new counter {counter}?') == 1:
                    try:
                        currTime = datetime.utcnow()

                        cursor.execute("INSERT INTO counters (name, timestamp, mentions) VALUES (%s, %s, %s)",(counter,currTime,0))
                        await ctx.send(f'Counter {counter} created.')
                    except:
                        raise FuckyError()
            else:
                raise InvalidArgument("That counter already exists!")
        
            database_disconnect(conn, cursor)

    @commands.is_owner()
    @commands.command(aliases=['removeCounter'],brief="Delete a counter.")
    async def deleteCounter(self,ctx: commands.Context, counter=None):
        if counter == None:
            raise InvalidArgument("You gotta tell me which one! <:angercry:757731437326762014>")
        
        else:
            conn, cursor = database_connect()
            counter = counter.lower()

            select_query = "SELECT * FROM counters WHERE name = %s"
            
            cursor.execute(select_query,(counter,))
            counters = cursor.fetchall()

            if len(counters) != 0:
                if (await confirmationMenu(self.client, ctx, f'Would you like to delete counter {counter}?') == 1):
                    cursor.execute("DELETE FROM counters WHERE name = %s",(counter,))
                    await ctx.send(f'Counter {counter} deleted.')
            else:
                raise InvalidArgument("That counter doesn't exist!")

            database_disconnect(conn, cursor)
            

    @commands.command(aliases=['counters','listCounters','allCounters','getCounters'],brief="List all counters.")
    async def viewCounters(self, ctx:commands.Context):
        counters = await run_query("SELECT * FROM counters ORDER BY mentions DESC")
        output = ""

        maxName = max([len(row[0]) for row in counters]) + 1
        maxNum = len(str(max([row[2] for row in counters])))

        for i in range(0,len(counters)):
            output += f'{(counters[i][0]+":").ljust(maxName)} {str(counters[i][2]).rjust(maxNum)} resets, last reset: {str(counters[i][1])[0:19]}\n'

        await ctx.send(f'```{output}```')
       
    @commands.command(aliases=['counter','seeCounter','counterInfo'],brief="View a counter.")
    async def viewCounter(self, ctx, counter=None):
        if counter == None:
            raise InvalidArgument("You have to tell me which one!")
        else:
            counter = counter.lower()

            counters = await run_query("SELECT * FROM counters WHERE name = '%s'",(counter,))
            
            if len(counters) == 0:
                raise InvalidArgument("That counter doesn't exist silly!")
            else:
                await ctx.send(f'{(counters[0][0]+":")} {counters[0][2]} resets, last reset: {str(counters[0][1])[0:19]}')
        
def setup(client):
    client.add_cog(Counters(client))
