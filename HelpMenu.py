import discord
from discord.ext import commands
from discord import Embed
import sys

import os

import asyncio
import checks
import functions
import json

DATABASE_URL = os.environ['DATABASE_URL']

baseEmbed = discord.Embed(title="HBS Help", description="HussieBot Oppression & More", color=0x005682)
baseEmbed.set_thumbnail(url="https://media.discordapp.net/attachments/753349219808444438/770918408371306516/hbs.png")
baseEmbed.set_footer(text="HBS is maintained by Vriska & Rose @ramblingArachnid#8781.")

def Merge(dict1, dict2):
    res = {**dict1, **dict2}
    return res


class HelpMenu(commands.Cog):
    def __init__(self, client):
        self.client = client
        with open('helpMenu.json') as f:
              self.data = json.load(f)


    @commands.command()
    async def helpi(self,ctx,option=None):
        data = self.data
        msg = await ctx.send("", embed=Embed.from_dict(Merge(data['base'],data['oldMenu'])))
        if option == "old":
            await self.displayOldHelp(msg, data['oldMenu'])

    async def displayMainHelp(self,msg):
        embed = msg.embeds[0]
        
    async def displayOldHelp(self, msg, fields):
        embed = from_dict(fields)
        await msg.edit(embed=embed)


def setup(client):
    client.add_cog(HelpMenu(client))
    
