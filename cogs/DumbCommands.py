import discord
from discord.ext import commands
import sys

import os

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
            
         
def setup(client):
    client.add_cog(DumbCommands(client))
