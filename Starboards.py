import discord
from discord.ext import commands
import time
from datetime import datetime, date

import sys

import os
import psycopg2
from psycopg2 import Error
from discord import NotFound

import asyncio

import checks

reactSem = asyncio.Semaphore(1)

colors = [0xa10000,0xa15000,0xa1a100, 0x658200, 0x416600, 0x008141, 0x008282, 0x005682, 0x000056, 0x2b0057, 0x6a006a, 0x77003c,0xff0000]


DATABASE_URL = os.environ['DATABASE_URL']

class Starboards(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        async with reactSem:
            if payload.emoji.name == "⭐":
                msg = await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id)
                await addToStarboard(msg)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        async with reactSem:
            if payload.emoji.name == "⭐":
                msg = await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id)
                reacts = msg.reactions
                count = 0
                for r in reacts:
                    if r.emoji == "⭐":
                        count = r.count
                
                nsfw = msg.channel.is_nsfw()

                conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM starboards WHERE nsfw=" + str(nsfw))
                board = cursor.fetchall()[0]
                starboardID = board[1]
                starlimit = board[4]
                starboardDBname = board[3]

                cursor.execute(f'SELECT * FROM {starboardDBname} WHERE msg = {msg.id}')
                row = cursor.fetchall()

                color = colors[max(0, min(count-starlimit,12))]
                
                stars = ["⭐","🌟","✨"]
                star = stars[min(count,10)//5]

                try: #TRY TO FIND MESSAGE IN STARBOARD DATABASE
                    smsg = await self.client.get_channel(starboardID).fetch_message(row[0][1])
                    update_query = f'UPDATE {starboardDBname} SET ns = {count}, time = %s WHERE msg = {msg.id}'

                    if count == 0: #DELETE STARRED MESSAGE IF STAR COUNT HITS ZERO. REMOVE FROM DATABASE.
                        cursor.execute(f'DELETE FROM {starboardDBname} WHERE msg = {msg.id}')
                        await smsg.delete()

                    else: #IF STAR COUNT IS NOT ZERO
                        cursor.execute(update_query, (datetime.fromtimestamp(time.time()),))

                        text = f'{star} **{count}** <#{msg.channel.id}>'
                        
                        embed_dict = smsg.embeds[0].to_dict()
                        embed_dict['color'] = color
                        embed = discord.Embed.from_dict(embed_dict)

                        await smsg.edit(content=text)
                        await smsg.edit(embed=embed)
                        
                except: #ELSE SEARCH THROUGH STARBOARD EMBEDS FOR MESSAGE ID
                    
                    id = 0
                    async for message in self.client.get_channel(starboardID).history(limit=4000):
                        if message.embeds[0].to_dict()['footer']['text'] == str(msg.id):
                            id = message.id
                            
                    if id != 0:
                        text = f'{star} **{count}** <#{msg.channel.id}>'
                        m = await self.client.get_channel(starboardID).fetch_message(id)
                        await m.edit(content=text)

                        embed_dict = m.embeds[0].to_dict()
                        embed_dict['color'] = color
                        embed = discord.Embed.from_dict(embed_dict)
                        await m.edit(embed=embed)

                
                conn.commit()
                cursor.close()
                conn.close()

    async def addToStarboard(self,msg,forceStar=False):
        reacts = msg.reactions
        count = 0
        for r in reacts:
            if r.emoji == "⭐":
                count = r.count
        
        nsfw = False
        if msg.channel.is_nsfw():
            nsfw = True

        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM starboards WHERE nsfw=" + str(nsfw))
        board = cursor.fetchall()[0]
        starboardID = board[1]
        starlimit = board[4]
        starboardDBname = board[3]

        cursor.execute(f'SELECT * FROM {starboardDBname} WHERE msg = {msg.id}')
        row = cursor.fetchall()

        color = colors[max(0, min(count-starlimit,12))]
        
        stars = ["⭐","🌟","✨"]
        star = stars[min(count,10)//5]
        
        edited = False #SET EDITED TO FALSE BY DEFAULT

    #IF MSG IN STARBOARD DATABASE, GET MESSAGE AND UPDATE. SET EDITED TO TRUE TO SKIP OTHER TESTS.
        try:
            smsg = await self.client.get_channel(starboardID).fetch_message(row[0][1])

            update_query = f'UPDATE {starboardDBname} SET ns = {count}, time = %s WHERE msg = {msg.id}'
            cursor.execute(update_query, (datetime.fromtimestamp(time.time()),))

            text = f'{star} **{count}** <#{msg.channel.id}>'

            embed_dict = smsg.embeds[0].to_dict()
            embed_dict['color'] = color
            embed = discord.Embed.from_dict(embed_dict)
            
            await smsg.edit(content=text,embed=embed)

            edited = True

        except:
            pass

    #IF STARRED MESSAGE NOT FOUND IN TABLE BUT THE COUNT IS OVER THE STAR LIMIT
        
        if edited == False and (count >= starlimit or forceStar):
            #SEARCH STARBOARD CHANNEL EMBEDS FOR ID.
            id = 0
            
            async for message in self.client.get_channel(starboardID).history(limit=4000):
                if message.embeds[0].to_dict()['footer']['text'] == str(msg.id):
                    id = message.id
                    
    #IF MESSAGE FOUND IN CHANNEL, UPDATE AND ADD TO TABLE. 
            if id != 0:
                text = f'{star} **{count}** <#{msg.channel.id}>'
                m = await self.client.get_channel(starboardID).fetch_message(id)
                await m.edit(content=text)

                embed_dict = m.embeds[0].to_dict()
                embed_dict['color'] = color
                embed = discord.Embed.from_dict(embed_dict)
                await m.edit(embed=embed)

    #ELSE CREATE NEW STARRED MESSAGE
            else:
                jumplink = f'[Jump!](https://discord.com/channels/609112858214793217/{payload.channel_id}/{msg.id})'

                embed = discord.Embed(description=msg.content, color=color, timestamp=msg.created_at,type="rich")
                embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar_url)
                embed.add_field(name="Source", value=jumplink, inline=True)
                try:
                    embed.set_image(url=str(msg.attachments[0].url))
                except:
                    pass
                embed.set_footer(text=str(msg.id))

                text = f'{star} **{count}** <#{msg.channel.id}>'
                smsg = await self.client.get_channel(starboardID).send(content=text, embed=embed)

                query = f'INSERT INTO {starboardDBname} (msg, smsg, ns, time) VALUES ({msg.id},{smsg.id},{count},%s)'
                cursor.execute(query, (datetime.fromtimestamp(time.time()),))

            

        conn.commit()
        cursor.close()
        conn.close()

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def star(self,ctx, id=None):
        if id == None:
            raise checks.InvalidArgument("Please include message ID or link.")
        elif str(id)[0:4] == "http":
            link = id.split('/')
            channel_id = int(link[6])
            msg_id = int(link[5])
            msg = await client.get_channel(channel_id).fetch_message(msg_id)
        else:
            for channel in ctx.guild.text_channels:
            try:
                msg = await channel.fetch_message(chId)
            except NotFound:
                continue

            if msg = None:
                raise checks.InvalidArgument("That message does not exist.")

        await addToStarboard(msg,True)
    
            
    '''@commands.command(pass_context=True)
    @commands.is_owner()
    async def sendStars(self,ctx: commands.Context,name=None):
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        if name==None:
            raise checks.InvalidArgument("Please include table name.")

        cursor.execute("SELECT * FROM {name}")

        starboard = cursor.fetchall()[0]

        starboard = tuple(starboard[x:x + 3] for x in range(0, len(starboard), 3))

        await ctx.send(str(starboard))

        conn.commit()
        cursor.close()
        conn.close()
    '''

    
                    
def setup(client):
    client.add_cog(Starboards(client))
