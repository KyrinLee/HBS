import discord
from discord.ext import commands
import sys
import re

import os
import psycopg2
from discord import NotFound

import time
from datetime import datetime, date

import asyncio

from modules import checks
from modules.functions import *
from resources.constants import *

postgreSQL_select_Query = "SELECT id FROM emoji"
update_q = "UPDATE emoji SET usage = %s WHERE id = %s"
get_usage = "SELECT usage FROM emoji WHERE id=%s"

class EmojiTracking(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        if not ctx.guild.id == SKYS_SERVER_ID:
            raise checks.WrongServer()
        return True

    async def on_message_emojis(self, message):
        await self.updateEmojiList(message.guild)
        try:
            conn, cursor = database_connect()
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
                                        
            database_disconnect(conn, cursor)
            
        except:
            raise

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.updateEmojiList(self.client.get_guild(payload.guild_id))

        conn, cursor = database_connect()
        cursor.execute(postgreSQL_select_Query)
        emojis = cursor.fetchall()

        emojis = [e[0] for e in emojis]

        if str(payload.emoji.id) in emojis:
            cursor.execute(get_usage,(str(payload.emoji.id),))
            use = cursor.fetchall()
            cursor.execute(update_q, (use[0][0]+1,str(payload.emoji.id)))
                                    
        database_disconnect(conn, cursor)

    @commands.command(pass_context=True,aliases=['geu'],brief="Get most and least used emojis.")
    async def getEmojiUsage(self, ctx, num=None, animated=None):
        async with ctx.channel.typing():
            if num == None:
                num = 15
            elif str(num)[0] in ["s","a"]:
                animated = num
                num = 15
            else:
                num = int(num)

            await self.updateEmojiList(ctx.guild)

            if animated == None:
                where_statement = ""
            elif animated[0] == "s":
                where_statement = "WHERE animated = FALSE"
            elif animated[0] == "a":
                where_statement = "WHERE animated = TRUE"
            else:
                where_statement = ""
                await ctx.send("Invalid static/animated argument. Showing all emoji.")

            emojis = await run_query(f'SELECT * FROM emoji {where_statement} ORDER BY usage DESC, name ASC')
            
            output = "`Top " + str(num) + " emojis:   ` "

            for i in range(0,num):
                    output += str(self.client.get_emoji(int(emojis[i][1])))
            output += "\n`Bottom " + str(num) + " emojis:` "

            for i in range(len(emojis)-1,len(emojis)-1-num,-1):
                    output += str(self.client.get_emoji(int(emojis[i][1])))

            if animated != None and animated[0] not in ["s","a"]:
                output += "\nShowing all emoji."
            elif animated[0] == "s":
                output+="\n(animated emojis excluded.)"
            elif animated[0] == "a":
                output+="\n(static emojis excluded.)"
                
            await ctx.send(output)

    @commands.command(pass_context=True, brief="Get usage data for specified emoji.")
    async def getEmojiUsageCount(self, ctx, emoji:discord.Emoji=None):
        data = await run_query(f'SELECT * FROM emoji WHERE name = \'{emoji.name}\'')
        await ctx.send(str(data[0][3]))
        
# ----- GET FULL EMOJI USAGE ----- #

    @commands.command(pass_context=True, aliases=['gfeu'], brief="Get all emoji usage data.")
    async def getFullEmojiUsage(self, ctx, animated=None):
        async with ctx.channel.typing():
            output = ""
            await self.updateEmojiList(ctx.guild)

            if animated == None:
                where_statement = ""
            elif animated[0] == "s" or animated[0:2] == "-s":
                where_statement = "WHERE animated = FALSE"
            elif animated[0] == "a" or animated[0:2] == "-a":
                where_statement = "WHERE animated = TRUE"
            else:
                where_statement = ""
                await ctx.send("Invalid static/animated argument. Showing all emoji.")

            data = await run_query(f'SELECT * FROM emoji {where_statement} ORDER BY usage DESC, name ASC')
            
            digits = [row[3] for row in data]
            count = 0
            maxDigits = 5

            for i in data:
                num = numberFormat(i[3])

                if self.client.get_emoji(int(i[1])).available == True:
                    output += str(self.client.get_emoji(int(i[1]))) + ":` " + (str(num)).rjust(maxDigits) + "` "
                    if count == 3:
                        output += "\n"
                        count = 0
                    else:
                        count = count + 1
                    
            if animated != None:
                if animated[0] == "s":
                    output+="\n(animated emojis excluded.)"
                if animated[0] == "a":
                    output+="\n(static emojis excluded.)"
                    
            await split_and_send(output, ctx.channel)
            
    async def updateEmojiList(self, guild):
        sql_insert_query = """ INSERT INTO emoji (name, id, animated, usage) VALUES (%s,%s,%s,%s)"""
        sql_delete_query = """ DELETE FROM emoji WHERE id = %s """
        emojis = guild.emojis
        newEmojis = []
        conn, cursor = database_connect()

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

        database_disconnect(conn, cursor)
    
    @commands.command(pass_context=True,brief="Update emoji list.")
    @commands.is_owner()
    async def updateEmojis(self, ctx):
        async with ctx.channel.typing():
            await self.updateEmojiList(ctx.guild)
            await ctx.send("Emoji List Updated.")

    @commands.command(pass_context=True,brief="Clears all emoji usage data.")
    @commands.is_owner()
    async def clearEmojiList(self, ctx):
        if (await checks.confirmationMenu(self.client, ctx, f'Would you like to clear all emoji usage data? This cannot be undone.') == 1):
            async with ctx.channel.typing():
                await run_query("DELETE FROM emoji")
                await ctx.send("Emoji list cleared.")

async def setup(client):
    await client.add_cog(EmojiTracking(client))
    
