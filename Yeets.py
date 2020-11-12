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

class Yeets(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == 609112858214793217:

            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()

            cursor.execute(select_q,("joinMsg",))
            joinmsg = str(cursor.fetchall()[0][0])

            cursor.execute(select_q,("yeetsChannel",))
            yeetsChannel = str(cursor.fetchall()[0][0])
            
            msg = joinmsg.replace("<name>",str(member.name))
            msg = msg.replace("<NAME>",str(member.name).upper())

            await self.client.get_channel(int(yeetsChannel)).send(msg)

            conn.commit()
            cursor.close()
            conn.close()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id == 609112858214793217:

            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()

            cursor.execute(select_q,("leaveMsg",))
            leavemsg = str(cursor.fetchall()[0][0])

            cursor.execute(select_q,("yeetsChannel",))
            yeetsChannel = str(cursor.fetchall()[0][0])
            
            msg = leavemsg.replace("<name>",str(member.name))
            msg = leavemsg.replace("<NAME>",str(member.name).upper())
            
            await self.client.get_channel(int(yeetsChannel)).send(msg)

            conn.commit()
            cursor.close()
            conn.close()

    @commands.command(pass_context=True,aliases=['changeMsg'],brief="Change join/leave messages.")
    @commands.is_owner()
    @checks.is_in_guild(609112858214793217)
    async def changeMessage(self,ctx: commands.Context,msgName=None,*,message):

        conn = psycopg2.connect(DATABASE_URL, sslmode='require')

        cursor = conn.cursor()

        if msgName == None:
            msgName = ""
        
        if msgName.lower() == "join" or msgName.lower() == "j":
            try:
                cursor.execute(update_q, (message,"joinMsg"))
                await ctx.send("Join Message changed to " + message)
                
            except:
                await ctx.send("An error occurred.")
            
        elif msgName.lower() == "leave" or msgName.lower() == "l":
            try:
                cursor.execute(update_q, (message,"leaveMsg"))
                await ctx.send("Leave Message changed to " + message)
                
            except:
                await ctx.send("An error occurred.")
        else:
            await ctx.send("Please specify `join` or `leave` (`j` or `l`)")

        conn.commit()
        cursor.close()
        conn.close()

    @commands.command(pass_context=True,aliases=['changeYeets','changeJoin','changeLeave'],brief="Change join/leave message channel.",)
    @commands.is_owner()
    @checks.is_in_guild(609112858214793217)
    async def changeYeetsChannel(self, ctx:commands.Context, channelID=None):

        conn = psycopg2.connect(DATABASE_URL, sslmode='require')

        cursor = conn.cursor()

        channelname = "test"

        if channelID == None:
            raise checks.InvalidArgument("Please include a numeric channel ID.")

        if channelID.isnumeric() == False:
            raise checks.InvalidArguments("Please include a numeric channel ID.")
            
        cid = int(channelID)
        for channel in ctx.guild.channels:
            if channel.id == cid:
                channelname = channel.name

                try:
                    cursor.execute(update_q,(str(cid),"yeetsChannel"))
                    await ctx.send("Join/Leave Message channel changed to " + str(channelname) + " (" + str(channel.id) + ").")
                             
                except:
                    await ctx.send("Database error occurred. Please Ping/DM ramblingArachnid#8781.")
                    
        if channelname == "test":
            raise checks.InvalidArgument(message="That channel is not in this server.")
          


        conn.commit()
        cursor.close()
        conn.close()
            
            
def setup(client):
    client.add_cog(Yeets(client))
