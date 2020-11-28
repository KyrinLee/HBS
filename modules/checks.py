import discord
from discord.ext import commands

import sys

import asyncio
from resources.constants import *

class NoDMs(commands.CheckFailure):
    pass
class WrongServer(commands.CheckFailure):
    pass
class NotVriska(commands.CheckFailure):
    pass

class FuckyError(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__.update(kwargs)


# ----- CHECK DEFINITIONS ----- #

def is_in_guild(guild_id):
    async def predicate(ctx):
        if ctx.guild == None:
            raise NoDMs()
        elif ctx.guild.id != guild_id:
            raise WrongServer()
        else:
            return True
    
    return commands.check(predicate)

def is_in_skys():
    return is_in_guild(SKYS_SERVER_ID)

def is_in_DMs():
    return commands.check(not commands.guild_only())
    
def is_vriska():
    async def predicate(ctx):
        if ctx.author.id != VRISKA_ID:
            raise commands.CheckFailure("Only Vriska can run this command for security reasons.")
        return True
    return commands.check(predicate)
