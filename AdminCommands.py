import discord
from discord.ext import commands
import sys

import os
import psycopg2
from psycopg2 import Error
from discord import NotFound

import json
import re

import asyncio
import checks

DATABASE_URL = os.environ['DATABASE_URL']

class AdminCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True,brief="Return json embed data.")
    @commands.is_owner()
    async def getEmbed(self, ctx:commands.Context, msgId):
        #SEARCH ALL CHANNELS FOR MESSAGE
        for channel in ctx.guild.text_channels:
            try:
                msg = await channel.fetch_message(msgId)
            except NotFound:
                continue

        #TRY TO RETURN JSON EMBED DATA
        try:
            dictionary = msg.embeds[0].to_dict()
            json_object = json.dumps(dictionary, indent = 4)   
            await ctx.send("```json\n" + json_object + "```")  
        except:
            raise checks.InvalidArgument("That's not a real message dummie. That or something else went fucky.")

    @commands.command(pass_context=True,brief="Copy starboard from one channel to another.",help="Transfers 1000 messages by default.")
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


    @commands.command(pass_context=True,brief="Create new Channel.",help="Category defaults to the category the command was sent in.\nTo set the channel as nsfw, include \"nsfw\" at the end of the command.")
    @commands.is_owner()
    async def createChannel(self,ctx: commands.Context,channelName=None, categoryID=None, nsfw=""):
        #IF NO CHANNEL NAME GIVEN
        if channelName==None:
            raise checks.InvalidArgument("I need a name for the channel dummie")

        #IF NO CATEGORY GIVEN, ASK IF THEY WOULD LIKE TO CREATE CHANNEL IN CONTEXT CATEGORY.
        if categoryID==None:
            result = await checks.confirmationMenu(self.client, ctx, f'Would you like to create a channel in {ctx.channel.category}?')
            if result == 1:
                categoryID = ctx.channel.category_id
            elif result == 0:
                raise checks.InvalidArgument("Operation cancelled. You can include a category id with hbs;createChannel <channelName> [categoryID] [nsfw].")
            else:
                raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")

        #IF NO CATEGORY ID GIVEN
        if categoryID != None:
            guild = ctx.message.guild
            cat = self.client.get_channel(categoryID)

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True),
                guild.get_member(707112913722277899): discord.PermissionOverwrite(read_messages=True)
            }

            await guild.create_text_channel(channelName, overwrites=overwrites, category=cat, nsfw=(nsfw=="nsfw"))



    @commands.command(pass_context=True,brief="Rename channel.")
    @commands.is_owner()
    async def renameChannel(self, ctx:commands.Context, channelId, newname):
        await self.client.get_channel(int(channelId)).edit(name=newname)

    @commands.command(pass_context=True,brief="Clear Channel.",help="Clears 0 messages by default.\nClears newest messages by default.")
    @commands.is_owner()
    async def clearChannel(self, ctx:commands.Context, channelID=None, numMessages=0, oldest="newest"):
        if channelID == None:
            raise checks.InvalidArgument("Please include a channel ID!")
        if numMessages == 0:
            raise checks.InvalidArgument("Default number of messages to clear is zero. Please specify number of messages.")
        if str(oldest).lower()[0] == 'n':
            oldest = False
        elif str(oldest).lower()[0] == 'o':
            oldest = True
        else:
            raise checks.InvalidArgument("Please specify whether you would like to clear 'old(est)' or 'new(est)' messages.")

        #CLEAR MESSAGES
        channel = self.client.get_channel(int(channelID))
        async for message in channel.history(limit=numMessages,oldest_first=oldest):
            try:
                await message.delete()
            except:
                continue

    @commands.command(pass_context=True,brief="Delete channel.")
    @commands.is_owner()
    async def deleteChannel(self, ctx:commands.Context, channelId):
        try:
            channelId = self.client.get_channel(int(channelId)).id
        except:
            raise checks.InvalidArgument("Channel not found.")
        
        result = await checks.confirmationMenu(self.client, ctx, f'Are you sure you would like to delete <#{channelId}>?')
        if result == 1:
            try:
                await self.client.get_channel(int(channelId)).delete()
                await ctx.send("Channel deleted.")
            except:
                raise checks.FuckyError("An error occurred.")
        elif result == 0:
            raise checks.InvalidArgument("Operation cancelled.")
        else:
            raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")

    @commands.command(pass_context=True,brief="Delete message.")
    @commands.is_owner()
    async def deleteMessage(self, ctx:commands.Context, msgId=None, channelId=None):
        if msgId == None:
            raise checks.InvalidArgument("You must include a message ID.")

        #get message
        m = await checks.getMessage(self.client, ctx, msgId, channelId)

        #get confirmation and delete
        result = await checks.confirmationMenu(self.client, ctx, f'Are you sure you would like to delete this message? `{m.clean_content[0:20]}...`',autoclear=True)
        if result == 1:
            try:
                await m.delete()
                await ctx.send("Message deleted.",delete_after=120.0)
            except:
                raise checks.FuckyError("An error occurred.")
        elif result == 0:
            raise checks.InvalidArgument("Operation cancelled.")
        else:
            raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")

    '''@commands.command(pass_context=True)
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
    '''

    @commands.command(pass_context=True,aliases=['nick'],brief="Change bot nickname.")
    @commands.is_owner()
    async def botnick(self, ctx, *, name):
        await ctx.guild.me.edit(nick=name)

    @commands.command(pass_context=True,aliases=['changeStatus'],brief="Change game in bot's status.")
    @commands.is_owner()
    async def changeGame(self, ctx, *, game):
        #CHANGE STATUS AND ADD TO DATABASE
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

    @commands.command(pass_context=True,enabled=False,brief="Dumps emoji table data.")
    @commands.is_owner()
    async def dump(self, ctx):
            connection = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = connection.cursor()

            cursor.execute("SELECT * FROM emoji")
            data = cursor.fetchall()

            await ctx.send(data)
            sys.stdout.write(data)
                    
            cursor.close()
            connection.close()

    @commands.command(pass_context=True,brief="Adds test stickbug emoji.")
    @commands.is_owner()
    async def addTestEmoji(self, ctx):
            with open("stickbug.gif", 'rb') as fd:
                await ctx.guild.create_custom_emoji(name='stickbug', image=fd.read())

    @commands.command(pass_context=True,brief="Deletes an emoji.")
    @commands.is_owner()
    async def deleteEmoji(self, ctx, emojiID):
            emoji = await ctx.guild.fetch_emoji(int(emojiID))
            await emoji.delete()
    

def setup(client):
    client.add_cog(AdminCommands(client))
        
