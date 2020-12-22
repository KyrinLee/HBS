import discord
from discord.ext import commands
import time
from datetime import datetime, date, timedelta

import sys

import os
import psycopg2

from psycopg2 import Error

from modules.checks import FuckyError
from modules import checks
from modules.functions import confirmationMenu, strfdelta

import asyncio
resetSem = asyncio.Semaphore(1)

from discord import InvalidArgument

DATABASE_URL = os.environ['DATABASE_URL']

class Counters(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['reset','update'],brief="Reset/Update a counter.")
    @checks.is_in_skys()
    async def resetCounter(self,ctx: commands.Context, *, counter=None):
        async with resetSem:
            if counter==None:
                raise InvalidArgument("I can't reset a counter if you don't tell me which one! <:angercry:757731437326762014>")
            
            connection = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = connection.cursor()

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
            

            connection.commit()
            cursor.close()
            connection.close()

        
    @commands.command(aliases=['addCounter'],brief="Create a new counter.")
    @checks.is_in_skys()
    async def newCounter(self,ctx: commands.Context, counter=None):

        if counter == None:
            raise InvalidArgument("You gotta name the counter! <:angercry:757731437326762014>")

        else:
            counter = counter.lower()
            #SEARCH DATABASE TO SEE IF COUNTER ALREADY EXISTS
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM counters WHERE name = %s",(counter,))
            counters = cursor.fetchall()

            #IF COUNTER DOESN'T EXIST, CREATE IT
            if len(counters) == 0:
                result = await confirmationMenu(self.client, ctx, f'Would you like to create new counter {counter}?')
                if result == 1:
                    try:
                        currTime = datetime.utcnow()

                        cursor.execute("INSERT INTO counters (name, timestamp, mentions) VALUES (%s, %s, %s)",(counter,currTime,0))
                        await ctx.send(f'Counter {counter} created.')
                    except:
                        raise FuckyError()
                elif result == 0:
                    await ctx.send("Counter creation cancelled.")
                else:
                    raise FuckyError("Something be fucky here. Idk what happened. Maybe try again?")
            else:
                raise InvalidArgument("That counter already exists!")
        
            conn.commit()
            cursor.close()
            conn.close()

    @commands.is_owner()
    @checks.is_in_skys()
    @commands.command(aliases=['removeCounter'],brief="Delete a counter.")
    async def deleteCounter(self,ctx: commands.Context, counter=None):
        if counter == None:
            raise InvalidArgument("You gotta tell me which one! <:angercry:757731437326762014>")
        
        else:
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()
            counter = counter.lower()

            select_query = "SELECT * FROM counters WHERE name = %s"
            
            cursor.execute(select_query,(counter,))
            counters = cursor.fetchall()

            if len(counters) != 0:
                result = await confirmationMenu(self.client, ctx, f'Would you like to delete counter {counter}?')
                if result == 1:
                    
                    cursor.execute("DELETE FROM counters WHERE name = %s",(counter,))
                    await ctx.send(f'Counter {counter} deleted.') 

                elif result == 0:
                    await ctx.send("Counter deletion cancelled.")
                else:
                    raise FuckyError("Something be fucky here. Idk what happened. Maybe try again?")
            else:
                raise InvalidArgument("That counter doesn't exist!")

            conn.commit()
            cursor.close()
            conn.close()
            

    @commands.command(aliases=['counters','listCounters','allCounters','getCounters'],brief="List all counters.")
    @checks.is_in_skys()
    async def viewCounters(self, ctx:commands.Context):
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM counters ORDER BY mentions DESC")
        counters = cursor.fetchall()

        maxName = max([len(row[0]) for row in counters]) + 1
        maxNum = len(str(max([row[2] for row in counters])))

        output = "```"

        for i in range(0,len(counters)):
            output += f'{(counters[i][0]+":").ljust(maxName)} {str(counters[i][2]).rjust(maxNum)} resets, last reset: {str(counters[i][1])[0:19]}\n'

        output += "```"

        await ctx.send(output)

        conn.commit()
        cursor.close()
        conn.close()

    @commands.command(aliases=['counter','seeCounter','counterInfo'],brief="View a counter.")
    @checks.is_in_skys()
    async def viewCounter(self, ctx, counter=None):
        if counter == None:
            raise InvalidArgument("You have to tell me which one!")
        else:
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()

            counter = counter.lower()

            cursor.execute("SELECT * FROM counters WHERE name = '%s'",(counter,))
            counters = cursor.fetchall()

            if len(counters) == 0:
                raise InvalidArgument("That counter doesn't exist silly!")
            else:
                await ctx.send(f'{(counters[0][0]+":")} {counters[0][2]} resets, last reset: {str(counters[0][1])[0:19]}')

    @commands.command(enabled=False)
    async def currTime(self, ctx):
        currTime = datetime.utcnow()
        await ctx.send(str(currTime))
        
def setup(client):
    client.add_cog(Counters(client))
