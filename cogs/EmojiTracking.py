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

from modules import checks, functions

DATABASE_URL = os.environ['DATABASE_URL']

class EmojiTracking(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            if checks.is_not_self(message.author.id) and checks.is_in_skys_id(message.guild.id) and message.webhook_id == None:
                
                await self.updateEmojiList(message.guild)
                
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

                for e in emojiIDs:
                    if e in oldEmojis:
                            cursor.execute(get_usage,(e,))
                            use = cursor.fetchall()
                            cursor.execute(update_q, (use[0][0]+1,e))
                                            
                connection.commit()                            
                cursor.close()
                connection.close()

        except:
            pass


    @commands.Cog.listener()
    @checks.is_in_skys()
    async def on_raw_reaction_add(self, payload):
        await self.updateEmojiList(self.client.get_guild(payload.guild_id))

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


    @commands.command(pass_context=True,aliases=['geu'],brief="Get most and least used emojis.")
    @checks.is_in_skys()
    async def getEmojiUsage(self, ctx, num=None, animated=None):
            if num == None:
                    num = 15
            elif str(num)[0] == "s" or str(num)[0] == "a":
                    animated = num
                    num = 15
            else:
                    num = int(num)

            if animated == None:
                animated = " "

            await self.updateEmojiList(ctx.guild)

            connection = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = connection.cursor()

            if animated[0] == "s":
                cursor.execute("SELECT * FROM emoji WHERE animated = FALSE ORDER BY usage DESC")
            elif animated[0] == "a":
                cursor.execute("SELECT * FROM emoji WHERE animated = TRUE ORDER BY usage DESC")
            else:
                if animated != " ":
                    await ctx.send("Invalid static/animated argument. Showing all emoji.")
                cursor.execute("SELECT * FROM emoji ORDER BY usage DESC")
           

            emojis = cursor.fetchall()
            output = "`Top " + str(num) + " emojis:   ` "

            for i in range(0,num):
                    output += str(self.client.get_emoji(int(emojis[i][1])))
            output += "\n`Bottom " + str(num) + " emojis:` "

            for i in range(len(emojis)-1,len(emojis)-1-num,-1):
                    output += str(self.client.get_emoji(int(emojis[i][1])))

                    
            if animated[0] == "s":
                    output+="\n(animated emojis excluded.)"
            if animated[0] == "a":
                    output+="\n(static emojis excluded.)"
            await ctx.send(output)

# ----- GET FULL EMOJI USAGE ----- #

    @commands.command(pass_context=True, aliases=['gfeu'], brief="Get all emoji usage data.")
    @checks.is_in_skys()
    async def getFullEmojiUsage(self, ctx, animated=None):
        await self.updateEmojiList(ctx.guild)
        
        connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = connection.cursor()
        if animated == None:
            animated = " "
            
        if animated[0] == "s":
            cursor.execute("SELECT * FROM emoji WHERE animated = FALSE ORDER BY usage DESC")
        elif animated[0] == "a":
            cursor.execute("SELECT * FROM emoji WHERE animated = TRUE ORDER BY usage DESC")
        else:
            if animated != " ":
                await ctx.send("Invalid static/animated argument. Showing all emoji.")
            cursor.execute("SELECT * FROM emoji ORDER BY usage DESC")

        data = cursor.fetchall()

        digits = [row[3] for row in data]

        output = ""
        count = 0
        maxDigits = 5

        letters = ["","k","m","b"]
        
        for i in data:
            num = functions.numberFormat(i[3])

            if self.client.get_emoji(int(i[1])).available == True:
                output += str(self.client.get_emoji(int(i[1]))) + ":` " + (str(num)).rjust(maxDigits) + "` "
                if count == 3:
                    output += "\n"
                    count = 0
                else:
                    count = count + 1
                
        if animated[0] == "s":
            output+="\n(animated emojis excluded.)"
        if animated[0] == "a":
            output+="\n(static emojis excluded.)"
                
        outputArr = functions.splitLongMsg(output)

        for o in outputArr:
            await ctx.send(o)

        connection.commit()
        cursor.close()
        connection.close()
            
    async def updateEmojiList(self, guild):
            
        connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = connection.cursor()
        
        sql_insert_query = """ INSERT INTO emoji (name, id, animated, usage) VALUES (%s,%s,%s,%s)"""
        sql_delete_query = """ DELETE FROM emoji WHERE id = %s """
        
        emojis = guild.emojis
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

        #TEMP DISABLED
        if guild.premium_tier > 0:
            for emoji in tbd:
                cursor.execute(sql_delete_query, (emoji,))

        for emoji in tba:
                e = self.client.get_emoji(int(emoji))
                record_to_insert = (e.name, str(e.id), e.animated, 0)
                cursor.execute(sql_insert_query, record_to_insert)

        connection.commit()
        cursor.close()
        connection.close()
            
    @commands.command(pass_context=True,brief="Update emoji list.")
    @commands.is_owner()
    @checks.is_in_skys()
    async def updateEmojis(self, ctx):

            await self.updateEmojiList(ctx.guild)
            await ctx.send("Emoji List Updated.")
            

    @commands.command(pass_context=True,brief="Clears all emoji usage data.")
    @commands.is_owner()
    async def clearEmojiList(self, ctx):
            result = await checks.confirmationMenu(self.client, ctx, f'Would you like to clear all emoji usage data? This cannot be undone.')
            if result == 1:
                connection = psycopg2.connect(DATABASE_URL, sslmode='require')
                cursor = connection.cursor()

                delete_query = "DELETE FROM emoji"
                cursor.execute(delete_query)
                connection.commit()
                await ctx.send("Emoji list cleared.")

                connection.commit()
                cursor.close()
                connection.close()
                
            elif result == 0:
                await ctx.send("Operation cancelled.")
            else:
                raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")

def setup(client):
    client.add_cog(EmojiTracking(client))
    
