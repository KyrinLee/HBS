import discord
from discord.ext import commands
import time
from datetime import datetime, date

import sys

import os
import psycopg2
from psycopg2 import Error
from discord import NotFound

import checks

DATABASE_URL = os.environ['DATABASE_URL']

class Starboards(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == "⭐":
            msg = await self.client.get_channel(payload.channel_id).fetch_message(payload.message_id)

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

            star = "⭐"
            if count >= 5:
                        star = "🌟"
            edited = False

            try:
                smsg = await self.client.get_channel(starboardID).fetch_message(row[0][1])
                update_query = f'UPDATE {starboardDBname} SET ns = {count}, time = %s WHERE msg = {msg.id}'
                cursor.execute(update_query, (datetime.fromtimestamp(time.time()),))

                text = f'{star} **{count}** <#{msg.channel.id}>'
                await smsg.edit(content=text)
                edited = True

            except:
                pass

            if edited == False and count >= starlimit:
                id = 0
                async for message in self.client.get_channel(starboardID).history(limit=4000):
                    if message.embeds[0].to_dict()['footer']['text'] == str(msg.id):
                        id = message.id
                        
                if id != 0:
                    text = f'{star} **{count}** <#{msg.channel.id}>'
                    m = await self.client.get_channel(starboardID).fetch_message(id)
                    await m.edit(content=text)

                else:
                    jumplink = f'[Jump!](https://discord.com/channels/609112858214793217/{payload.channel_id}/{msg.id})'

                    embed = discord.Embed(description=msg.content, color=0x005682, timestamp=msg.created_at,type="rich")
                    embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar_url)
                    embed.add_field(name="Source", value=jumplink, inline=True)
                    try:
                        embed.set_image(message.attachments[0].url)
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

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def createChannel(self,ctx: commands.Context,channelName=None, nsfw=""):
        
        if channelName==None:
            raise checks.InvalidArgument("Please include a channel name.")

        guild = ctx.message.guild

        cat = ctx.channel.category

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            guild.get_member(707112913722277899): discord.PermissionOverwrite(read_messages=True)
        }

        await guild.create_text_channel(channelName, overwrites=overwrites, category=cat, nsfw=(nsfw=="nsfw"))


    @commands.command(pass_context=True)
    @commands.is_owner()
    async def getEmbed(self, ctx:commands.Context, chId):
        for channel in ctx.guild.text_channels:
            try:
                msg = await channel.fetch_message(chId)
            except NotFound:
                continue
        try:
            await ctx.send(str(msg.embeds[0].to_dict()))
        except:
            await ctx.send("Message not found.")


    @commands.command(pass_context=True)
    @commands.is_owner()
    async def transferStarboard(self, ctx:commands.Context, sourceChId, targetChId, lim=1000):
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        async for message in self.client.get_channel(int(sourceChId)).history(limit=lim, oldest_first=True):
            try:
                s = message.content.split(" ")[1]
                smsg = await self.client.get_channel(int(targetChId)).send(content=message.content,embed=message.embeds[0])
                q = f'INSERT INTO test VALUES ({message.id},{smsg.id},{s},%s)'
                cursor.execute(q, (datetime.fromtimestamp(time.time()),))
                
            except:
                continue

        conn.commit()
        cursor.close()
        conn.close()

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def clearChannel(self, ctx:commands.Context):
        async for message in ctx.channel.history(limit=10,oldest_first=True):
            try:
                await message.delete()
            except:
                continue

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def renameChannel(self, ctx:commands.Context, channelId, newname):
        await self.client.get_channel(int(channelId)).edit(name=newname)

    @commands.command(pass_context=True, enabled=False)
    @commands.is_owner()
    async def deleteChannel(self, ctx:commands.Context, channelId):
        await self.client.get_channel(int(channelId)).delete()

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def makeChannelPublic(self, ctx:commands.Context, channelId, lewd=""):
        if lewd == "unlewd":
            nsfw=False
        elif lewd == "lewd":
            nsfw=True
        else:
            nsfw=self.client.get_channel(int(channelId)).is_nsfw()
        await self.client.get_channel(int(channelId)).edit(nsfw=nsfw)
        await self.client.get_channel(int(channelId)).set_permissions(ctx.guild.default_role, read_messages=True)
        await self.client.get_channel(int(channelId)).set_permissions(ctx.guild.default_role, send_messages=False)
                    
def setup(client):
    client.add_cog(Starboards(client))
