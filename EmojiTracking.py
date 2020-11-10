import discord
from discord.ext import commands
import sys
import re

import os
import psycopg2
from psycopg2 import Error
from discord import NotFound

import time
from datetime import datetime, date

import asyncio
import checks
import functions

DATABASE_URL = os.environ['DATABASE_URL']

class EmojiTracking(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild.id == 609112858214793217 and message.author.id != 753345733377261650 and message.webhook_id is None:

            connection = psycopg2.connect(DATABASE_URL, sslmode='require')

            cursor = connection.cursor()
            postgreSQL_select_Query = "SELECT id FROM emoji"
            update_q = "UPDATE emoji SET usage = %s WHERE id = %s"
            get_usage = "SELECT usage FROM emoji WHERE id=%s"

            cursor.execute(postgreSQL_select_Query)
            oldEmojis = cursor.fetchall()

            oldEmojis = [e[0] for e in oldEmojis]

            emojis = re.findall(r'<:\w*:\d*>', message.content)
            emojisA = re.findall(r'<a:\w*:\d*>', message.content)

            for i in range(0, len(emojisA)):
                emojis.append(emojisA[i])
            #print(emojis)
            emojiIDs = []

            for i in range(0, len(emojis)):
                emojiIDs.append(emojis[i].split(":")[2].replace('>', ''))

            cursor.execute("SELECT * FROM vars WHERE name = 'lastemojiupdate'")
            lastEmojiUpdate = cursor.fetchall()[0][1];
            
            channel = self.client.get_channel(754527915290525807)
            #sys.stdout.write(str(lastEmojiUpdate))
            
            currTime = datetime.fromtimestamp(time.time())
            
            date = str(currTime)[0:10];
            #sys.stdout.write(date);

            if str(lastEmojiUpdate) != date:
                cursor.execute("UPDATE vars set value = %s WHERE name = 'lastemojiupdate'", (date,))
                await updateEmojiList(message)

            for e in emojiIDs:
                if e in oldEmojis:
                        cursor.execute(get_usage,(e,))
                        use = cursor.fetchall()
                        cursor.execute(update_q, (use[0][0]+1,e))
                                        
            connection.commit()                            
            cursor.close()
            connection.close()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        conn = psycopg2.connect(DATABASE_URL, sslmode='require')

        cursor = conn.cursor()
        postgreSQL_select_Query = "SELECT id FROM emoji"
        update_q = "UPDATE emoji SET usage = %s WHERE id = %s"
        get_usage = "SELECT usage FROM emoji WHERE id=%s"

        cursor.execute(postgreSQL_select_Query)
        emojis = cursor.fetchall()

        emojis = [e[0] for e in emojis]

        if str(payload.emoji.id) in emojis:
            cursor.execute(get_usage,(str(payload.emoji.id),))
            use = cursor.fetchall()
            cursor.execute(update_q, (use[0][0]+1,str(payload.emoji.id)))
                                    
        conn.commit()                            
        cursor.close()
        conn.close()


    @commands.command(pass_context=True,aliases=['geu'])
    async def getEmojiUsage(self, ctx, num=None, animated=None):
            if num == None:
                    num = 15
            elif num == "-s" or num == "-a":
                    animated = num
                    num = 15
            else:
                    num = int(num)

            connection = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = connection.cursor()

            if animated == "-s":
                    cursor.execute("SELECT * FROM emoji WHERE animated = FALSE ORDER BY usage DESC")
            elif animated == "-a":
                    cursor.execute("SELECT * FROM emoji WHERE animated = TRUE ORDER BY usage DESC")
            else:
                    cursor.execute("SELECT * FROM emoji ORDER BY usage DESC")

            emojis = cursor.fetchall()
            output = "Top " + str(num) + " emojis: "

            for i in range(0,num):
                    output += str(self.client.get_emoji(int(emojis[i][1])))
            output += "\nBottom " + str(num) + " emojis: "

            for i in range(len(emojis)-1,len(emojis)-1-num,-1):
                    output += str(self.client.get_emoji(int(emojis[i][1])))

                    
            if animated == "-s":
                    output+="\n(animated emojis excluded.)"
            if animated == "-a":
                    output+="\n(static emojis excluded.)"
            await ctx.send(output)


    @commands.command(pass_context=True,aliases=['gfeu'])
    async def getFullEmojiUsage(self, ctx):
            
            connection = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM emoji ORDER BY usage DESC")

            data = cursor.fetchall()

            digits = [row[3] for row in data]

            output = ""
            count = 0
            maxDigits = len(str(max(digits)))

            await ctx.send(str(maxDigits))
            
            for i in data:
                output += str(self.client.get_emoji(int(i[1]))) + ": " + (str(i[3]).rjust(maxDigits))

                if count == 4:
                    output += "\n"
                    count = 0
                else:
                    output += "  "
                    count = count + 1
                    
            outputArr = functions.splitLongMsg(output)

            for o in outputArr:
                await ctx.send("```"+ o + "```")

            connection.commit()
            cursor.close()
            connection.close()
            
    async def updateEmojiList(self, message):
            
            connection = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = connection.cursor()
            
            sql_insert_query = """ INSERT INTO emoji (name, id, animated, usage) VALUES (%s,%s,%s,%s)"""
            sql_delete_query = """ DELETE FROM emoji WHERE id = %s """
            
            emojis = message.guild.emojis
            newEmojis = []

            i = 0
            for emoji in emojis:
                            newEmojis.append(str(emoji.id))
                            i+=1

            postgreSQL_select_Query = "SELECT * FROM emoji"

            cursor.execute(postgreSQL_select_Query)
            tempEmojis = cursor.fetchall()

            oldEmojis = []
            for e in tempEmojis:
                    oldEmojis.append(e[1])
            
            tbd = list(sorted(set(oldEmojis) - set(newEmojis)))
            tba = list(sorted(set(newEmojis) - set(oldEmojis)))

            channel = self.client.get_channel(754527915290525807)
            #await channel.send("TBD: " + str(len(tbd)))
            #await channel.send("TBA: " + str(len(tba)))

            delCount = 0
            addCount = 0

            for emoji in tbd:
                    cursor.execute(sql_delete_query, (emoji,))
                    await channel.send(f'Emoji {emoji} deleted.')
                    delCount += 1

            for emoji in tba:
                    e = self.client.get_emoji(int(emoji))
                    record_to_insert = (e.name, str(e.id), e.animated, 0)
                    cursor.execute(sql_insert_query, record_to_insert)
                    await channel.send(f'Emoji {emoji} added.')
                    addCount = addCount + 1

            connection.commit()
            cursor.close()
            connection.close()
            
    @commands.command(pass_context=True)
    @checks.is_in_guild(609112858214793217)
    async def updateEmojis(self, ctx,description="Updates emoji list for current guild (Limited to Sky's Server.)"):

            await updateEmojiList(ctx.message)
            await ctx.send("Emoji List Updated.")
            

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def clearEmojiList(self, ctx,hidden=True,description="Clears emoji usage data."):
            connection = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = connection.cursor()

            if ctx.message.author.id == 707112913722277899:
                    delete_query = "DELETE FROM emoji"
                    cursor.execute(delete_query)
                    connection.commit()
                    await ctx.send("Emoji list cleared.")

            else:
                    await ctx.send("You do not have the permissions for this command.")

            connection.commit()
            cursor.close()
            connection.close()



def setup(client):
    client.add_cog(EmojiTracking(client))
    
