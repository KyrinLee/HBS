import discord
from discord.ext import commands
import sys

import os
import psycopg2
from psycopg2 import Error
from discord import NotFound

import json

import asyncio
import checks

DATABASE_URL = os.environ['DATABASE_URL']

class AdminCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def createChannel(self,ctx: commands.Context,channelName=None, nsfw=""):
        
        if channelName==None:
            raise checks.InvalidArgument("I need a name for the channel dummie")

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
            dictionary = msg.embeds[0].to_dict()
            json_object = json.dumps(dictionary, indent = 4)   
            await ctx.send("```json\n" + json_object + "```")  
        except:
            raise checks.InvalidArgument("That's not a real message dummie")

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
    async def clearChannel(self, ctx:commands.Context, channelID):
        async for message in self.client.get_channel(int(channelID)).history(limit=1,oldest_first=False):
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
    async def deleteMessage(self, ctx:commands.Context, channelId, msgId):
        m = await self.client.get_channel(int(channelId)).fetch_message(int(msgId))
        await m.delete()

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

    @commands.command(pass_context=True,aliases=['nick'])
    @commands.is_owner()
    async def botnick(self, ctx, *, name, hidden=True, description="Changes bot nickname in current guild."):
        await ctx.guild.me.edit(nick=name)

    @commands.command(pass_context=True,aliases=['cg'])
    @commands.is_owner()
    async def changeGame(self, ctx, *, game, hidden=True, description="Changes \"currently playing\" text."):
        try:
            await self.client.change_presence(activity=discord.Game(name=game))
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()
            cursor.execute("UPDATE vars SET value = %s WHERE name = 'game'",(game,))
        except:
            raise checks.FuckyError()
        finally:
            conn.commit()
            cursor.close()
            conn.close()

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def dump(self, ctx, hidden=True, description="Dumps emoji table data."):
            connection = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM emoji")
            data = cursor.fetchall()

            await ctx.send(data)
            sys.stdout.write(data)
                    
            cursor.close()
            connection.close()

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def addTestEmoji(self, ctx):
            with open("stickbug.gif", 'rb') as fd:
                await ctx.guild.create_custom_emoji(name='stickbug', image=fd.read())

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def deleteEmoji(self, ctx, id):
            emoji = await ctx.guild.fetch_emoji(int(id))
            await emoji.delete()

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def getChannelPerms(self, ctx):
        m = await (ctx.guild.fetch_member(753345733377261650))
        sys.stdout.write(str(ctx.channel.permissions_for(m)))
        

def setup(client):
    client.add_cog(AdminCommands(client))
        
