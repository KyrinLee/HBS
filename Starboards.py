import discord
from discord.ext import commands
import sys

import os
import psycopg2

from psycopg2 import Error

import checks

DATABASE_URL = os.environ['DATABASE_URL']

starboardID = 771463560366391356

class Starboards(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == "⭐":
            msg = payload.message.id
            smsg = self.client.get_channel(starboardID).send("x")

            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()

            sbnum = 0

            cursor.execute("SELECT * FROM starboard")
            data = cursor.fetchall()

            i = 0
            j = 0
            
            while i < len(data):
                if j == 5:
                    i = i+1
                    j = 0
                if data[i][3*j] == "":
                    sbnum = i
                        break
                j = j+1

            if sbnum == 0:
                raise InvalidArgument("Something went really wrong here.")

            sbstr = str(sbnum)
            vars = (sbstr, sbstr, sbstr, str(msg.id), str(smsg.id), 2)

            cursor.execute("INSERT INTO starboard (msg%s, smsg%s, ns%s) VALUES (%s, %s, %s)", vars)

            conn.commit()
            cursor.close()
            conn.close()
            
    @commands.command(pass_context=True)
    @commands.is_owner()
    async def sendStars(self,ctx: commands.Context):
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM starboard")

        starboard = cursor.fetchall()

        ctx.send(str(starboard))

        starboard = tuple(starboard[x:x + 3] for x in range(0, len(starboard), 3))

        ctx.send(str(starboard))

        conn.commit()
        cursor.close()
        conn.close()

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def createChannel(self,ctx: commands.Context,channelName=None):
        if channelName==None:
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
