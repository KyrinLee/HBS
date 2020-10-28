import discord
from discord.ext import commands
import sys

import os
from hbs import is_admin

joinmsg = os.environ['joinMsg']
leavemsg = os.environ['leaveMsg']
yeetsChannel = os.environ['yeetsChannel']

DATABASE_URL = os.environ['DATABASE_URL']

class Yeets(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(member):
        if member.guild.id == 609112858214793217:
            msg = joinmsg.replace("<name>",str(member.name))
            msg = joinmsg.replace("<NAME>",str(member.name).upper())
            await client.get_channel(yeetsChannel).send(msg)

    @commands.Cog.listener()
    async def on_member_remove(member):
        if member.guild.id == 609112858214793217:
            msg = leavemsg.replace("<name>",str(member.name))
            msg = leavemsg.replace("<NAME>",str(member.name).upper())
            await client.get_channel(yeetsChannel).send(msg)

    @commands.command()
    @is_admin(ctx.author.id)
    async def changeMsg(self,ctx,msgName=None,*,message):
        if msgName == None:
            msgName = ""
        
        if msgName.lower() == "join" or msgName.lower() == "j":
            os.environ.set('joinMsg',message)
            joinmsg = os.environ['joinMsg']
            ctx.send("Join Message changed to " + joinmsg)
        elif msgName.lower() == "leave" or msgName.lower() == "l":
            os.environ.set('leaveMsg',message)
            joinmsg = os.environ['leaveMsg']
            ctx.send("Leave Message changed to " + leavemsg)
        else:
            ctx.send("Please specify `join` or `leave` (`j` or `l`)")

def setup(client):
    client.add_cog(Yeets(client))
