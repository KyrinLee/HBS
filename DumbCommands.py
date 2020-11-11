import discord
from discord.ext import commands
import sys

import os

import random as rd
from math import trunc, floor

import checks

DATABASE_URL = os.environ['DATABASE_URL']

class DumbCommands(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.command(pass_context=True,aliases=["what is my ","what's my "],brief="Get your bounty.")
    async def bounty(self, ctx: commands.Context, user:commands.clean_content=""):
        if user=="":
            user = ctx.author.display_name
        elif user[0] == '@':
            user = user[1:]
        val = "0"
        num = rd.random()*100
        num2 = rd.random()*100
        num3 = rd.random()*100

        funnynouns = ["emus", "cold mcdonald's french fries", "lives", "arms and legs", "teeth", "ducks"]
        normalnouns = ["dollars", "cents", "pennies"]
        phrases = ["$69,420,666","12 goats. Take it or leave it.","Firstborn Child",
                   "37 eels in a trenchcoat"":)","Oh, you know.",
                   "It is decidedly so.", "Reply hazy, try again.",
                   "Signs point to yes.", "Negative 12",
                   "It's a secret.", "Wouldn't you like to know?"]
        if num < 50:
            noun = ""
            if num2 < 70:
                noun = rd.choice(normalnouns)
            else:
                noun = rd.choice(funnynouns)

            if num3 < 30:
                val = str(floor(rd.gauss(50,50))) + " " + noun
            else:
                val = str(abs(floor(rd.gauss(50,50)))) + " " + noun
        elif num < 90:
            val = "$" + str(abs(round(rd.gauss(100,8000),2)))

        else:
            val = rd.choice(phrases)
        
        
        await ctx.send(f'{user}\'s bounty: {val}')
                 
            
def setup(client):
    client.add_cog(DumbCommands(client))
