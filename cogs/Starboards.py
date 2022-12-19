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

from modules import checks
from modules.functions import *
from resources.constants import *

reactSem = asyncio.Semaphore(1)

class Starboards(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        if not ctx.guild.id == SKYS_SERVER_ID:
            raise checks.WrongServer()
        return True

    async def add_to_starboard(self,msg,starboardDBname=None,forceStar=False):
        reacts = msg.reactions

        count = 0
        emojis = [stars[0]]

        if starboardDBname in starboards:

            if starboardDBname == "lewdboard":
                emojis = [stars[1]]
            elif starboardDBname == "moodboard":
                emojis = moodreacts
            elif starboardDBname == "cursedboard":
                emojis = cursedreacts
    
            for r in reacts:
                for e in emojis:
                    if str(r.emoji) == e:
                        count = r.count

            data = await run_query("SELECT * FROM starboards WHERE tablename= %s", (str(starboardDBname),))
            board = data[0]
            starboardID = board[1]
            starlimit = board[4]
            starboardDBname = board[3]

            if starlimit == 0:
                return 

            row = await run_query(f'SELECT * FROM {starboardDBname} WHERE msg = {msg.id}')
            
            star = str(stars[min(count,10)//5]) if starboardDBname == "starboard" else emojis[0]
            
            edited = False #SET EDITED TO FALSE BY DEFAULT

            #IF MSG IN STARBOARD DATABASE, GET MESSAGE AND UPDATE. SET EDITED TO TRUE TO SKIP OTHER TESTS.
            try:
                smsgid = row[0][1]
                smsg = await self.client.get_channel(starboardID).fetch_message(row[0][1])
                if smsgid != None and smsg == None:
                    await self.client.get_channel(HBS_CHANNEL_ID).send("Vriska actually needs to fix something. Please ping ASAP. A starboard record references a message that no longer exists.")

                
                if count == 0: #DELETE STARRED MESSAGE IF STAR COUNT HITS ZERO. REMOVE FROM DATABASE.
                    await run_query(f'DELETE FROM {starboardDBname} WHERE msg = {msg.id}')
                    await smsg.delete()
                    edited = True
                else:
                    update_query = f'UPDATE {starboardDBname} SET ns = {count}, time = %s WHERE msg = {msg.id}'
                    await run_query(update_query, (datetime.fromtimestamp(time.time()),))

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
                    if len(message.embeds) > 0 and message.embeds[0].to_dict()['footer']['text'] == str(msg.id):
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
                    await run_query(query, (datetime.fromtimestamp(time.time()),))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        async with reactSem:
            if (payload.guild_id != SKYS_SERVER_ID):
                return
            msg = await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id)
            starboardDBname = ""
            
            if msg.channel.is_nsfw() or payload.emoji.name == stars[1]:
                starboardDBname = "lewdboard"
            elif str(payload.emoji) in cursedreacts:
                starboardDBname = "cursedboard"
            elif str(payload.emoji) in moodreacts:
                if msg.channel.category_id != VENT_CATEGORY_ID or msg.channel.id == POSITIVE_VENT_CHANNEL_ID:
                    starboardDBname = "moodboard"
            elif payload.emoji.name == stars[0]:
                starboardDBname = "starboard"

            if starboardDBname != "":
                await self.add_to_starboard(msg, starboardDBname=starboardDBname)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        async with reactSem:
            if (payload.guild_id != SKYS_SERVER_ID):
                return
            msg = await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id)
            starboardDBname = ""
            
            if msg.channel.is_nsfw() or payload.emoji.name == stars[1]:
                starboardDBname = "lewdboard"
            elif str(payload.emoji) in cursedreacts:
                starboardDBname = "cursedboard"
            elif str(payload.emoji) in moodreacts:
                if msg.channel.category_id != VENT_CATEGORY_ID or msg.channel.id == POSITIVE_VENT_CHANNEL_ID:
                    starboardDBname = "moodboard"
            elif payload.emoji.name == stars[0]:
                starboardDBname = "starboard"

            if starboardDBname != "":
                await self.add_to_starboard(msg, starboardDBname=starboardDBname)
            
    @commands.command(pass_context=True, brief="Manually star a message.", help="Starboard defaults to 'starboard'.")
    @commands.is_owner()
    async def star(self,ctx, messageIDorLink=None, starboard="starboard"):
        msg = await getMessage(self.client, ctx, messageIDorLink)

        if starboard not in starboards:
            raise TypeError("That starboard does not exist.")

        await self.add_to_starboard(msg,forceStar=True,starboardDBname=starboard)

    @commands.command(pass_context=True, aliases=['moveStarboard','changeStarboardChannel'], brief="Change a starboard channel.",help="Starboard defaults to 'starboard'.")
    @commands.is_owner()
    async def changeStarboard(self,ctx,starboard="starboard",channelID=None):
        if starboard not in starboards:
            raise TypeError(f'Please include a valid starboard name from the following: {str(starboards)[1:len(str(starboards))-1]}')
        elif channelID == None:
            raise TypeError("Please include message ID or link.")

        channel = self.client.get_channel(channelID)
        if await confirmationMenu(self.client, ctx, f'Would you like to change the {starboard} to channel {channel}?') == 1:
            await run_query(f'UPDATE starboards SET channelid = {channelID} WHERE name = {starboard}')
            await ctx.send(f'{starboard.capitalize()} channel has been updated to {channel}.')

    @commands.command(aliases=['starboardInfo'],brief="View all starboard settings.",help="Use mobile selector -m for a more readable format on mobile.")
    @commands.is_owner()
    async def viewStarboards(self, ctx:commands.Context,mobile=""):
        starboards = await run_query("SELECT * FROM starboards")
        
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

    @commands.command(brief="Change threshold for a starboard.",help="Starboard defaults to 'starboard'.\nSet starlimit to 0 to disable starboard.")
    @commands.is_owner()
    async def changeStarlimit(self,ctx,starboard="starboard",starlimit=-1):
        if starlimit == -1:
            raise TypeError("Please include new star limit or 0 to disable.")
        elif starboard not in starboards:
            raise TypeError(f'Please include a valid starboard name from the following: {str(starboards)[1:len(str(starboards))-1]}')

        if starlimit == 0:
            await confirmationMenu(self.client, ctx, f'Would you like to disable {starboard}?')
        else:
            await confirmationMenu(self.client, ctx, f'Would you like to change the {starboard} starlimit to {starlimit}?')
        
        await run_query(f'UPDATE starboards SET starlimit = {starlimit} WHERE name = \'{starboard}\'')
        if starlimit == 0:
            await ctx.send(f'{starboard.capitalize()} has been disabled. Simply set this starboard\'s limit to above 0 to re-enable.')
        else:
            await ctx.send(f'{starboard.capitalize()} starlimit has been updated to {starlimit}.')

    @commands.command(brief="Disable a starboard.",help="Starboard defaults to 'starboard'.")
    @commands.is_owner()
    async def disableStarboard(self,ctx,starboard="starboard"):
        if starboard not in starboards:
            raise TypeError(f'Please include a valid starboard name from the following: {str(starboards)[1:len(str(starboards))-1]}')
        await ctx.invoke(self.client.get_command('changeStarlimit'), starboard=starboard, starlimit = 0)

    @commands.command(brief="Enable a starboard.",help="Starboard defaults to 'starboard'.")
    @commands.is_owner()
    async def enableStarboard(self,ctx,starboard="starboard",starlimit=None):
        if starboard not in starboards:
            raise TypeError(f'Please include a valid starboard name from the following: {str(starboards)[1:len(str(starboards))-1]}')
        if not starlimit.isdigit():
            raise TypeError("Please include a valid integer star limit for the starboard.")

        await ctx.invoke(self.client.get_command('changeStarlimit'), starboard=starboard, starlimit = int(starlimit))

    '''async def purgeStarboards(self,oldTime):
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        output = ""

        cursor.execute(f'SELECT * FROM starboard WHERE time < \'{oldTime}\'')
        starboard_purge_data = cursor.fetchall()
    
        for i in range(0,len(starboard_purge_data)):
            output += str(starboard_purge_data[i]) + "\n"

        await self.client.get_channel(754527915290525807).send(output)

        conn.commit()
        cursor.close()
        conn.close()
        '''
    
    @commands.command(pass_context=True,brief="Copy starboard from one channel to another.",help="Transfers 1000 messages by default.")
    @commands.is_owner()
    async def transferStarboard(self, ctx:commands.Context, sourceChId, targetChId, lim=1000):
        async with ctx.channel.typing():
            async for message in self.client.get_channel(int(sourceChId)).history(limit=lim, oldest_first=True):
                try:
                    s = message.content.split(" ")[1]
                    smsg = await self.client.get_channel(int(targetChId)).send(content=message.content,embed=message.embeds[0])
                    q = f'INSERT INTO test VALUES ({message.id},{smsg.id},{s},%s)'
                    await run_query(q, (datetime.fromtimestamp(time.time()),))
                    
                except:
                    continue
                
async def setup(client):
    await client.add_cog(Starboards(client))
