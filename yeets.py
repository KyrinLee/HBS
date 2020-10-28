import discord
from discord.ext import commands
import sys

import os

global joinmsg = os.environ['joinMsg']
global leavemsg = os.environ['leaveMsg']
global yeetsChannel = os.environ['yeetsChannel']

DATABASE_URL = os.environ['DATABASE_URL']

class Yeets(commands.Cog):
    def __init__(self, client):
        self.client = client

    @client.event
    async def on_member_join(member):
        if member.guild.id == 609112858214793217:
            msg = joinmsg.replace("<name>",str(member.name))
            await client.get_channel(yeetsChannel).send(msg)

    @client.event 
    async def on_member_remove(member):
        if member.guild.id == 609112858214793217:
            msg = leavemsg.replace("<name>",str(member.name))
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
