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

stars = ["\U00002B50","\U0001F31F","\U00002728"]
moodreacts = ["\U0001F91D","<:bigmood:713218567977304146>"]

starboards = ["starboard","lewdboard","moodboard"]

DATABASE_URL = os.environ['DATABASE_URL']

class Starboards(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def addToStarboard(self,msg,starboardDBname=None,forceStar=False):
        reacts = msg.reactions

        count = 0
        emojis = [stars[0]]

        if starboardDBname in starboards:

            if starboardDBname == "lewdboard":
                emojis = [stars[1]]
            elif starboardDBname == "moodboard":
                emojis = moodreacts
    
            for r in reacts:
                for e in emojis:
                    if str(r.emoji) == e:
                        count = r.count

            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM starboards WHERE tablename= '" + str(starboardDBname) + "'")

            board = cursor.fetchall()[0]
            starboardID = board[1]
            starlimit = board[4]
            starboardDBname = board[3]

            cursor.execute(f'SELECT * FROM {starboardDBname} WHERE msg = {msg.id}')
            row = cursor.fetchall()

            color = colors[max(0, min(count-starlimit,12))]
            
            star = str(stars[min(count,10)//5]) if starboardDBname == "starboard" else emojis[0]
            
            edited = False #SET EDITED TO FALSE BY DEFAULT

            #IF MSG IN STARBOARD DATABASE, GET MESSAGE AND UPDATE. SET EDITED TO TRUE TO SKIP OTHER TESTS.
            try:
                smsgid = row[0][1]
                smsg = await self.client.get_channel(starboardID).fetch_message(row[0][1])
                if smsgid != None and smsg == None:
                    await self.client.get_channel(754527915290525807).send("Vriska actually needs to fix something. Please ping ASAP. A starboard record references a message that no longer exists.")

                
                if count == 0: #DELETE STARRED MESSAGE IF STAR COUNT HITS ZERO. REMOVE FROM DATABASE.
                    cursor.execute(f'DELETE FROM {starboardDBname} WHERE msg = {msg.id}')
                    await smsg.delete()
                    edited = True
                else:
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
                    jumplink = f'[Jump!](https://discord.com/channels/609112858214793217/{msg.channel.id}/{msg.id})'

                    embed = discord.Embed(description=msg.content+"\n", color=color, timestamp=msg.created_at,type="rich")
                    embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar_url)
                    embed.add_field(name="Source", value=jumplink, inline=True)
                    try:
                        if not msg.attachments[0].is_spoiler():
                            embed.set_image(url=str(msg.attachments[0].url))
                        else:
                            embed.description = embed.description + "(spoiled image, jump to message to view)"
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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        async with reactSem:
            msg = await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id)
            starboardDBname = ""
            
            if msg.channel.is_nsfw() or payload.emoji.name == stars[1]:
                starboardDBname = "lewdboard"
            elif str(payload.emoji) in moodreacts:
                starboardDBname = "moodboard"
            elif payload.emoji.name == stars[0]:
                starboardDBname = "starboard"

            if starboardDBname != "":
                await self.addToStarboard(msg, starboardDBname=starboardDBname)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        async with reactSem:
            msg = await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id)
            starboardDBname = ""
            
            if msg.channel.is_nsfw() or payload.emoji.name == stars[1]:
                starboardDBname = "lewdboard"
            elif str(payload.emoji) in moodreacts:
                starboardDBname = "moodboard"
            elif payload.emoji.name == stars[0]:
                starboardDBname = "starboard"

            if starboardDBname != "":
                await self.addToStarboard(msg, starboardDBname=starboardDBname)
            
    @commands.command(pass_context=True, brief="Manually star a message.")
    @commands.is_owner()
    async def star(self,ctx, id=None, starboard=""):
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
                    msg = await channel.fetch_message(id)
                except NotFound:
                    continue

            if msg == None:
                raise checks.InvalidArgument("That message does not exist.")

        if board not in starboards:
            raise checks.InvalidArgument("That starboard does not exist.")

        await self.addToStarboard(msg,forceStar=True,board=starboard)

    @commands.command(pass_context=True, aliases=['moveStarboard','changeStarboardchannel'], brief="Change a starboard channel.")
    @commands.is_owner()
    async def changeStarboard(self,ctx,id=None,board="starboard"):
        lewd = True if (lewd == lewd or nsfw) else False
            
        if id == None:
            raise checks.InvalidArgument("Please include message ID or link.")

        if board.find("lewd") != -1:
            starboard = "lewdboard"
        elif board.find("mood") != -1:
            starboard = "moodboard"
        else:
            starboard = "starboard"
        
        channel = self.client.get_channel(id)
        result = await checks.confirmationMenu(self.client, ctx, f'Would you like to change the {starboard} to channel {channel}?')
        if result == 1:
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()
            cursor.execute(f'UPDATE starboards SET channelid = {id} WHERE name = {starboard}')
            await ctx.send(f'{starboard.capitalize()} channel has been updated to {channel}.')

            conn.commit()
            cursor.close()
            conn.close()

        elif result == 0:
            await ctx.send("Operation cancelled.")
        else:
            raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")

    @commands.command(pass_context=True, brief="Change lewdboard channel.",hidden=True)
    @commands.is_owner()
    async def changeLewdboard(self,ctx, id=None):
        if id == None:
            raise checks.InvalidArgument("Please include message ID or link.")
        await self.changeStarboard(ctx,id,True)

    @commands.command(aliases=['starboards','starboardInfo'],brief="View all starboard settings.")
    @commands.is_owner()
    async def viewStarboards(self, ctx:commands.Context,mobile=""):
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM starboards")
        starboards = cursor.fetchall()

        maxName = max([len(row[0]) for row in starboards])
        maxChannelName = max([len(str(self.client.get_channel(int(row[1])))) for row in starboards])
        
        output = "```STARBOARD".ljust(maxName)+ " | " + "CHANNEL".ljust(maxChannelName+22) + " | NSFW  | STAR LIMIT \n" if mobile != "-m" else ""

        for i in range(0,len(starboards)):
            channel = self.client.get_channel(starboards[i][1])
            if mobile == "-m":
                output += f'**{starboards[i][0]}**\n#{channel.name} ({channel.id})\nNSFW: {str(starboards[i][2])}\nSTAR LIMIT: {str(starboards[i][4])}\n\n'
            else:
                output += f'{(starboards[i][0]).ljust(maxName)} | #{channel.name.ljust(maxChannelName)} ({channel.id}) | {str(starboards[i][2]).ljust(5)} | {str(starboards[i][4]).rjust(10)}\n'

        output = (output + "```") if mobile != "-m" else output

        await ctx.send(output)

        conn.commit()
        cursor.close()
        conn.close()


    @commands.command(brief="Change threshold for a starboard.")
    @commands.is_owner()
    async def changeStarLimit(self,ctx,starlimit=-1,lewd=False):
        if starlimit == -1:
            raise checks.InvalidArgument("Please include new star limit.")
        else:
            starboard = "lewdboard" if lewd else "starboard"
            
            result = await checks.confirmationMenu(self.client, ctx, f'Would you like to change the {starboard} starlimit to {starlimit}?')
            if result == 1:
                conn = psycopg2.connect(DATABASE_URL, sslmode='require')
                cursor = conn.cursor()
                cursor.execute(f'UPDATE starboards SET starlimit = {starlimit} WHERE name = \'{starboard}\'')
                await ctx.send(f'{starboard.capitalize()} starlimit has been updated to {starlimit}.')

                conn.commit()
                cursor.close()
                conn.close()

            elif result == 0:
                await ctx.send("Operation cancelled.")
            else:
                raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")
    
                    
def setup(client):
    client.add_cog(Starboards(client))
