import discord
from discord.ext import commands
import sys

import os
import psycopg2

from psycopg2 import Error

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

            joinmsg = cursor.execute(select_q,("joinMsg",))[0][0]
            
            await self.client.get_channel(int(yeetsChannel)).send(joinmsg)
            
            msg = joinmsg.replace("<name>",str(member.name))
            msg = joinmsg.replace("<NAME>",str(member.name).upper())

            await self.client.get_channel(int(yeetsChannel)).send(msg)

            conn.commit()
            cursor.close()
            conn.close()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild.id == 609112858214793217:

            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()

            leavemsg = cursor.execute(select_q,("leaveMsg",))[0][0]
            await self.client.get_channel(int(yeetsChannel)).send(leavemsg)
            
            msg = leavemsg.replace("<name>",str(member.name))
            msg = leavemsg.replace("<NAME>",str(member.name).upper())
            
            await self.client.get_channel(int(yeetsChannel)).send(msg)

            conn.commit()
            cursor.close()
            conn.close()

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def changeMsg(self,ctx: commands.Context,msgName=None,*,message):

        conn = psycopg2.connect(DATABASE_URL, sslmode='require')

        cursor = conn.cursor()

        if msgName == None:
            msgName = ""
        
        if msgName.lower() == "join" or msgName.lower() == "j":
            #try:
                cursor.execute(update_q, ("joinMsg",message))
                await ctx.send("Join Message changed to " + joinmsg)
                
            #except:
                #await ctx.send("An error occurred.")
            
        elif msgName.lower() == "leave" or msgName.lower() == "l":
            #try:
                cursor.execute(update_q, ("leaveMsg",message))
                await ctx.send("Leave Message changed to " + leavemsg)
                
            #except:
                #await ctx.send("An error occurred.")
        else:
            await ctx.send("Please specify `join` or `leave` (`j` or `l`)")

        conn.commit()
        cursor.close()
        conn.close()
            
def setup(client):
    client.add_cog(Yeets(client))
