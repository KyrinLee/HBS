import discord
from discord.ext import commands

import asyncio

class InvalidArgument(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__.update(kwargs)

class FuckyError(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__.update(kwargs)

class CheckFailure(commands.CommandError):
    def __init__(self, *args, **kwargs):
        msg = kwargs.pop('msg',None)
        super().__init__(*args,**kwargs)
        self.__dict__.update(kwargs)

# ----- CHECK DEFINITIONS ----- #

def is_in_guild(guild_id):
    async def predicate(ctx):
        if ctx.guild == None:
            return False
        elif ctx.guild.id != guild_id:
            return False
        else:
            return True
    return commands.check(predicate)

def is_in_skys():
    async def predicate(ctx):
        return ctx.guild and ctx.guild.id == 609112858214793217
    return commands.check(predicate)

def is_not_webhook():
    async def predicate(ctx):
        if ctx.author.webhook_id == None:
            return True
        else:
            return False
    return commands.check(predicate)

def is_in_skys_id(id):
    if id != 609112858214793217:
        #raise CheckFailure("You can't run that here! <:angercry:757731437326762014>")
        return False
    else:
        return True

def is_not_self(id):
    if id == 753345733377261650:
        return False
    else:
        return True

