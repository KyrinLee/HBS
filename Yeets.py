import discord
from discord.ext import commands
import sys

import os

joinmsg = os.environ['joinMsg']
leavemsg = os.environ['leaveMsg']
yeetsChannel = os.environ['yeetsChannel']

DATABASE_URL = os.environ['DATABASE_URL']

class Yeets(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(member):
        await client.get_channel(754527915290525807).send(str(member.guild.id))
        await client.get_channel(int(yeetsChannel)).send("Yay I recognized *something* leaving")
        if member.guild.id == 609112858214793217:
            await client.get_channel(int(yeetsChannel)).send("So the guild thingy is fine.")
            msg = joinmsg.replace("<name>",str(member.name))
            msg = joinmsg.replace("<NAME>",str(member.name).upper())
            await client.get_channel(int(yeetsChannel)).send(msg)

    @commands.Cog.listener()
    async def on_member_remove(member):
        await client.get_channel(754527915290525807).send(str(member.guild.id))
        await client.get_channel(int(yeetsChannel)).send("Yay I recognized *something* leaving")
        if member.guild.id == 609112858214793217:
            await client.get_channel(int(yeetsChannel)).send("So the guild thingy is fine.")
            msg = leavemsg.replace("<name>",str(member.name))
            msg = leavemsg.replace("<NAME>",str(member.name).upper())
            await client.get_channel(int(yeetsChannel)).send(msg)

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def changeMsg(self,ctx: commands.Context,msgName=None,*,message):
        if msgName == None:
            msgName = ""
        
        if msgName.lower() == "join" or msgName.lower() == "j":
            os.environ['joinMsg'] = message
            joinmsg = os.environ['joinMsg']
            await ctx.send("Join Message changed to " + joinmsg)
        elif msgName.lower() == "leave" or msgName.lower() == "l":
            os.environ['leaveMsg'] = message
            leavemsg = os.environ['leaveMsg']
            await ctx.send("Leave Message changed to " + leavemsg)
        else:
            await ctx.send("Please specify `join` or `leave` (`j` or `l`)")
            
def setup(client):
    client.add_cog(Yeets(client))
