import discord
from discord.ext import commands
import sys

import psycopg2
from psycopg2 import Error

import json
import re

import asyncio

from modules.checks import FuckyError
from modules import checks
from modules.functions import getMessage, confirmationMenu, splitLongMsg
from discord import InvalidArgument

from resources.constants import *

class AdminCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True,brief="Return json embed data.")
    @commands.is_owner()
    async def getEmbed(self, ctx:commands.Context, msgIDorLink):
        #SEARCH ALL CHANNELS FOR MESSAGE
        async with ctx.channel.typing():
            msg = await getMessage(self.client, ctx, msgIDorLink)

            #TRY TO RETURN JSON EMBED DATA
            try:
                dictionary = msg.embeds[0].to_dict()
                json_object = json.dumps(dictionary, indent = 4)   
                await ctx.send("```json\n" + json_object + "```")  
            except:
                raise InvalidArgument("That's not a real message dummie. That or something else went fucky.")


    @commands.command(pass_context=True,brief="Create new Channel.",help="Category defaults to the category the command was sent in.\nTo set the channel as nsfw, include \"nsfw\" at the end of the command.")
    @commands.is_owner()
    async def createChannel(self,ctx: commands.Context,channelName=None, categoryID=None, nsfw=""):
        #IF NO CHANNEL NAME GIVEN
        if channelName==None:
            raise InvalidArgument("I need a name for the channel dummie")

        #IF NO CATEGORY GIVEN, ASK IF THEY WOULD LIKE TO CREATE CHANNEL IN CONTEXT CATEGORY.
        if categoryID==None:
            result = await confirmationMenu(self.client, ctx, f'Would you like to create a channel in {ctx.channel.category}?')
            if result == 1:
                categoryID = ctx.channel.category_id
            elif result == 0:
                raise InvalidArgument("Operation cancelled. You can include a category id with hbs;createChannel <channelName> [categoryID] [nsfw].")
            else:
                raise FuckyError("Something be fucky here. Idk what happened. Maybe try again?")

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
        async with ctx.channel.typing():
            if channelID == None:
                raise InvalidArgument("Please include a channel ID!")
            if numMessages == 0:
                raise InvalidArgument("Default number of messages to clear is zero. Please specify number of messages.")
            if str(oldest).lower()[0] == 'n':
                oldest = False
            elif str(oldest).lower()[0] == 'o':
                oldest = True
            else:
                raise InvalidArgument("Please specify whether you would like to clear 'old(est)' or 'new(est)' messages.")

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
            raise InvalidArgument("Channel not found.")
        
        result = await confirmationMenu(self.client, ctx, f'Are you sure you would like to delete <#{channelId}>?')
        if result == 1:
            try:
                await self.client.get_channel(int(channelId)).delete()
                await ctx.send("Channel deleted.")
            except:
                raise FuckyError("An error occurred.")
        elif result == 0:
            raise InvalidArgument("Operation cancelled.")
        else:
            raise FuckyError("Something be fucky here. Idk what happened. Maybe try again?")

    @commands.command(pass_context=True,brief="Delete message.")
    @commands.is_owner()
    async def deleteMessage(self, ctx:commands.Context, msgIDorLink=None, channelId=None):
        if msgIDorLink == None:
            raise InvalidArgument("You must include a message ID.")

        async with ctx.channel.typing():
            #get message
            m = await getMessage(self.client, ctx, msgIDorLink, channelId)

            #get confirmation and delete
            result = await confirmationMenu(self.client, ctx, f'Are you sure you would like to delete this message? `{m.clean_content[0:20]}...`',autoclear=True)
            if result == 1:
                try:
                    await m.delete()
                    await ctx.send("Message deleted.",delete_after=120.0)
                except:
                    raise FuckyError("An error occurred.")
            elif result == 0:
                raise InvalidArgument("Operation cancelled.")
            else:
                raise FuckyError("Something be fucky here. Idk what happened. Maybe try again?")

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
        if name in [None, "", "clear","c"]:
            name = None
            output = "Bot nickname cleared."
        else:
            output = f'Bot name changed to {name}'

        await ctx.guild.me.edit(nick=name)
        await ctx.send(output)

    @commands.command(pass_context=True,aliases=['changeStatus'],brief="Change game in bot's status.")
    @commands.is_owner()
    async def changeGame(self, ctx, *, game):
        async with ctx.channel.typing():
            #CHANGE STATUS AND ADD TO DATABASE
            try:
                await self.client.change_presence(activity=discord.Game(name=game))
                conn, cursor = database_connect()
                cursor.execute("UPDATE vars SET value = %s WHERE name = 'game'",(game,))
            except:
                raise FuckyError()
            finally:
                database_disconnect(conn, cursor)
            await ctx.send(f'HBS\'s status game changed to {game}.')

    @commands.command(pass_context=True,brief="Adds test stickbug emoji.")
    @commands.is_owner()
    async def addTestEmoji(self, ctx):
        with open("resources/stickbug.gif", 'rb') as fd:
            await ctx.guild.create_custom_emoji(name='stickbug', image=fd.read())
            await ctx.send("Emoji created.")

    @commands.command(pass_context=True,brief="Deletes an emoji.")
    @commands.is_owner()
    async def deleteEmoji(self, ctx, emojiID):
        emoji = await ctx.guild.fetch_emoji(int(emojiID))
        await emoji.delete()
        await ctx.send("Emoji deleted.")

    @commands.command(pass_context=True,brief="Run a database query.")
    @checks.is_vriska()
    async def sql(self, ctx, *, query=""):
        conn, cursor = database_connect()

        cursor.execute(query)
        data = cursor.fetchall()

        await split_and_send(str(data), ctx.channel, char=',')
        database_disconnect(conn, cursor)

    @commands.command(pass_context=True, aliases=["disable tupper", "disableTupperbox","disable tupperbox"], brief="Disables Tupperbox.")
    async def disableTupper(self,ctx):
        async with ctx.channel.typing():
            tupper = ctx.guild.get_member(TUPPERBOX_ID)
            pk_down_role = ctx.guild.get_role(PK_DOWN_ROLE_ID)
            shupperbox_role = ctx.guild.get_role(SHUPPERBOX_ROLE_ID)
            await tupper.remove_roles(pk_down_role)
            await tupper.add_roles(shupperbox_role)
            await ctx.channel.send("Tupperbox disabled.")

    @commands.command(pass_context=True, aliases=["enable tupper", "enableTupperbox", "enable tupperbox"], brief="Enables Tupperbox.")
    async def enableTupper(self,ctx):
        async with ctx.channel.typing():
            tupper = ctx.guild.get_member(TUPPERBOX_ID)
            pk_down_role = ctx.guild.get_role(PK_DOWN_ROLE_ID)
            shupperbox_role = ctx.guild.get_role(SHUPPERBOX_ROLE_ID)
            await tupper.add_roles(pk_down_role)
            await tupper.remove_roles(shupperbox_role)
            await ctx.channel.send("Tupperbox enabled.")
    
    
def setup(client):
    client.add_cog(AdminCommands(client))
        
