import discord
from discord.ext import commands
import sys

import os
import psycopg2

from psycopg2 import Error

from modules import checks
from modules.functions import *

DATABASE_URL = os.environ['DATABASE_URL']

select_q = "SELECT value FROM vars WHERE name = %s"
update_q = "UPDATE vars SET value = %s WHERE name = %s"

class Yeets(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == 609112858214793217:
            
            conn, cursor = database_connect()
            cursor.execute(select_q,("joinMsg",))
            joinmsg = str(cursor.fetchall()[0][0])

            cursor.execute(select_q,("yeetsChannel",))
            yeetsChannel = str(cursor.fetchall()[0][0])
            
            database_disconnect(conn, cursor)
            
            msg = joinmsg.replace("<name>",str(member.name))
            msg = msg.replace("<NAME>",str(member.name).upper())

            if msg != "":
                await self.client.get_channel(int(yeetsChannel)).send(msg)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id == 609112858214793217:

            conn, cursor = database_connect()

            cursor.execute(select_q,("leaveMsg",))
            leavemsg = str(cursor.fetchall()[0][0])

            cursor.execute(select_q,("yeetsChannel",))
            yeetsChannel = str(cursor.fetchall()[0][0])

            database_disconnect(conn, cursor)
            
            msg = leavemsg.replace("<name>",str(member.name))
            msg = msg.replace("<NAME>",str(member.name).upper())
            
            if msg != "":
                await self.client.get_channel(int(yeetsChannel)).send(msg)

    @commands.command(pass_context=True,aliases=['changeMessage','changeMsg'],brief="Change join/leave messages.",
                      help="Message example: '\u003cname\u003e has left the server.'\nUse \u003cname\u003e for default capitalization, or \u003cNAME\u003e for all caps.\nLeave message blank to disable join/leave message.")
    @commands.is_owner()
    @checks.is_in_guild(609112858214793217)
    async def changeYeetsMessage(self,ctx: commands.Context,msgName=None,*,message=""):

        if msgName == None:
            raise discord.InvalidArgument("Please specify 'join' or 'leave' message.")
        if message == None:
            message = ""

        if msgName.lower()[0] == "j":
            messageName = "Join Message"
            columnName = "joinMsg"
        elif msgName.lower()[0] == "l":
            messageName = "Leave Message"
            columnName = "leaveMsg"

        if message != "":
            cursor.execute(update_q, (message,columnName))
            await ctx.send(f'{messageName} changed to `{message}`.')
        else:
            result = await confirmationMenu(self.client, ctx, f'Would you like to delete the current {messageName.lower()}?')
            if result == 1:
                await run_query(update_q, (message,columnName))
                await ctx.send(f'{messageName} deleted. To reinstate {messageName.lower()}s, just run this command again with a non-empty {messageName.lower()}.')
            elif result == 0:
                await ctx.send("Operation cancelled.")
            else:
                raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")

    @commands.command(pass_context=True,aliases=['changeYeets','changeJoin','changeLeave'],brief="Change join/leave message channel.",)
    @commands.is_owner()
    @checks.is_in_guild(609112858214793217)
    async def changeYeetsChannel(self, ctx:commands.Context, channelID=None):
        channelname = "test"

        if channelID == None or channelID.isnumeric() == False:
            raise discord.InvalidArgument("Please include a numeric channel ID.")

        cid = int(channelID)
        for channel in ctx.guild.channels:
            if channel.id == cid:
                channelname = channel.name

                try:
                    await run_query(update_q,(str(cid),"yeetsChannel"))
                    await ctx.send("Join/Leave Message channel changed to " + str(channelname) + " (" + str(channel.id) + ").")
                             
                except:
                    await ctx.send("Database error occurred. Please Ping/DM ramblingArachnid#8781.")
                    
        if channelname == "test":
            raise discord.InvalidArgument(message="That channel is not in this server.")
            
            
def setup(client):
    client.add_cog(Yeets(client))
