import discord
from discord.ext import commands
import sys

import os

import asyncio

import random as rd
from math import trunc, floor

from modules import checks
from modules.functions import nsyl

from resources.constants import *

import inflect

p = inflect.engine()


DATABASE_URL = os.environ['DATABASE_URL']

class DumbCommands(commands.Cog):
    def __init__(self, client):
        self.client = client


    @commands.command(pass_context=True,brief="Get your bounty.")
    async def bounty(self, ctx: commands.Context, *, user:commands.clean_content=""):
        await asyncio.sleep(1)
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

    @commands.command(pass_context=True,brief="Get a random classpect.")
    async def classpect(self, ctx, *, user:commands.clean_content=""):
        await asyncio.sleep(1)
        async with ctx.channel.typing():
            if user=="":
                user = ctx.author.display_name
            elif user[0] == '@':
                user = user[1:]

            with open("resources/nouns.txt") as f:
                nouns = [line.rstrip('\n') for line in f]

                def get_word_with_syllable_count(count):
                    word = ""
                    while nsyl(word) != [count]:
                        word = rd.choice(nouns)
                    if p.singular_noun(word) == False:
                        return word
                    return p.singular_noun(word)
                    
                '''def get_word_with_syllable_count(count):
                    word = ""
                    while (nsyl(word) != [count]):
                        word = rd.choice(list(dictionary.keys()))
                    return word
                '''
                
                word1 = get_word_with_syllable_count(1)
                word2 = get_word_with_syllable_count(1)
            
        await ctx.send(f'{user} is a {word1.capitalize()} of {word2.capitalize()}.')
    @commands.command(pass_context=True,brief="Generates a ship.", aliases=["shippingchart","shipping"])
    async def ship(self, ctx, *, user:commands.clean_content=""):
        await asyncio.sleep(1)
        if user=="":
            user = rd.choice(homestuck_characters).split(" ")[0]
        elif user in ["me","Me","ME"]:
            user = ctx.author.display_name
        elif user[0] == '@':
            user = user[1:]

        if user == "<@!480855402289037312>":
            await ctx.send("He and I are in a vacillating \U00002665/\U00002660 relationship! Obviously.")
        elif user == "<@!753345733377261650>":
            await ctx.send("My quadrants are reserved solely for <@!480855402289037312>.")
        else:
            name = rd.choice(homestuck_characters)
            quadrant = rd.choice(["\U00002660","\U00002665","\U00002666","\U00002663"])
            await ctx.send(f'{user}{quadrant}{name.split(" ")[0]}')

    @commands.command(pass_context=True, brief="Get your blood color!", aliases=["hemospec","bloodcolor","blood"])
    async def hemospectrum(self, ctx, user:commands.clean_content=""):
        if user=="":
            user = ctx.author.display_name
        elif user[0] == '@':
            user = user[1:]

        color = rd.choice(hearts)
        await ctx.send(f'{user}\'s blood color is {color} ({color.lstrip("<:Heart_").split("_")[0]}')
            
    @commands.command(pass_context=True,brief="Sends bubblewrap message.")
    async def bubblewrap(self, ctx, size="5x5"):
        await asyncio.sleep(1)
        dimensions = re.split('x| ',size)
        try:
            width = int(dimensions[0])
            height = int(dimensions[1])
        except:
            raise checks.InvalidArgument("Invalid size! Run hbs;bubblewrap for a 5x5 grid, or specify a grid size like this: hbs;bubblewrap 9x9")
        output = "Bubble Wrap!\n\n" + (("||pop||" * width + "\n") * height)
        output = output.rstrip("\n")
        if len(output) > 2000:
            await ctx.send("Unfortunately discord's message character limit doesn't support bubble wrap that size :( \nHere's what I could fit!") 
            outputArr = splitLongMsg(output, 2000)
            output = outputArr[0]
        await ctx.send(output)

    @commands.command(pass_context=True,brief="Sends list of HussieBot's currently blacklisted phrases.")
    async def hussieBlacklist(self, ctx):
        await asyncio.sleep(1)
        output = "Currently Blacklisted Phrases: \n"
        for phrase in bannedPhrases:
            output += phrase + "\n"

        output = output.rstrip("\n")
        await ctx.send(output)


    @commands.command(pass_context=True,brief="Sends a number of whitespace lines to clear a channel.", help="Use 'permanent' or a specified number of hours for auto-deletion.")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def whitespace(self, ctx, delete_after=8):
        await asyncio.sleep(1)
        try:
            int(delete_after.rstrip('h'))
        except ValueError:
            if delete_after[0] in ["p", "s"]:
                delete_after = -1
            else:
                delete_after = 8
            
        output = "```"
        output += (' '.join(random.choices(starsList + spaces, k=900)))

        hours = None if delete_after == -1 else int(delete_after) * 3600
        await ctx.send(output + "```",delete_after=hours)

        
    @commands.command(pass_context=True,brief="Vriska.")
    async def vriska(self, ctx):
        await ctx.send("<:vriska:776019724956860417>")
        await ctx.message.delete()

def setup(client):
    client.add_cog(DumbCommands(client))
