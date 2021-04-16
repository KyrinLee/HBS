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

from modules.functions import *
from resources.constants import *

from discord import InvalidArgument

class AdminCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True,brief="Return json embed data.",enabled=False)
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
                await run_query("UPDATE vars SET value = %s WHERE name = 'game'",(game,))
            except:
                raise FuckyError()
            
            await ctx.send(f'HBS\'s status game changed to {game}.')

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
        
