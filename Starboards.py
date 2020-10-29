import discord
from discord.ext import commands
import sys

import os
import psycopg2

from psycopg2 import Error

import checks

DATABASE_URL = os.environ['DATABASE_URL']

select_q = "SELECT value FROM vars WHERE name = %s"
update_q = "UPDATE vars SET value = %s WHERE name = %s"

class Starboards(commands.Cog):
    def __init__(self, client):
        self.client = client

    #@commands.Cog.listener()
    #async def on_member_join(self, member):

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def createChannel(self,ctx: commands.Context,channelName=None):
        if channelName=None:
            raise checks.InvalidArgument("Please include a channel name.")

        guild = ctx.message.guild

        cat = ctx.channel.category

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            guild.get_member(707112913722277899): discord.PermissionOverwrite(read_messages=True)
        }

        await guild.create_text_channel(channelName, overwrites=overwrites, category=cat)

        

            
def setup(client):
    client.add_cog(Starboards(client))
