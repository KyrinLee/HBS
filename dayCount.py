import discord
from discord.ext import commands
import time
from datetime import datetime, date

import sys

import os
import psycopg2

from psycopg2 import Error

DATABASE_URL = os.environ['DATABASE_URL']

class dayCount(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def reset(self,ctx: commands.Context, counter:str):
        connection = psycopg2.connect(DATABASE_URL, sslmode='require')

        cursor = connection.cursor()

        currTime = date.fromtimestamp(time.time())

        cursor.execute("CREATE TABLE IF NOT EXISTS counters (name VARCHAR(255) UNIQUE, timestamp TIMESTAMP, mentions INT)")

        try:
            cursor.execute("INSERT INTO counters (name, timestamp, mentions) VALUES (%s, %s, %s)",(counter,currTime,0))
            await ctx.send("counter " + counter + " created.")
        except:
            cursor.close()
            connection.close()

            connection = psycopg2.connect(DATABASE_URL, sslmode='require')

            cursor = connection.cursor()
            cursor.execute("SELECT * FROM counters WHERE name=%s",(counter,))
            data = cursor.fetchall()

            mentions = data[0][2]
            timeStamp = data[0][1]
            
            cursor.execute("UPDATE counters SET timestamp=%s, mentions=%s WHERE name=%s",(currTime,mentions,counter))

            timeDiff = currTime - timeStamp
            await ctx.send("counter " + counter + " updated - it has been " + str(timeDiff) + " seconds since this counter was last reset.")

        connection.commit()
        cursor.close()
        connection.close()

def setup(client):
    client.add_cog(dayCount(client))
