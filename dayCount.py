import discord
from discord.ext import commands
import time
from datetime import datetime, date

class dayCount():
    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True)
    async def reset(ctx, counter):
        connection = psycopg2.connect(DATABASE_URL, sslmode='require')

        cursor = connection.cursor()

        currTime = time.time()

        cursor.execute("CREATE TABLE IF NOT EXISTS counters (name VARCHAR(255) UNIQUE, timestamp TIMESTAMP, mentions INT")

        try:
            cursor.execute("INSERT INTO counters (name, timestamp, mentions) VALUES (%s, %s, %s)",(name,currTime,0))
            await ctx.send("counter " + name + " created.")
        except:
            cursor.execute("SELECT * FROM counters WHERE name=%s",(name,))
            data = cursor.fetchall()

            mentions = data[0][2]
            timeStamp = data[0][1]
            
            cursor.execute("UPDATE counters SET timestamp=%s, mentions=%s WHERE name=%s",(currTime,mentions,name))

            timeDiff = datetime.combine(date.min, currTime) - datetime.combine(date.min, timeStamp)
            await ctx.send("counter " + name + " updated - it has been " + str(timeDiff) + " seconds since this counter was last reset.")

def setup(client):
    client.add_cog(dayCount(client))
