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
        super().__init__(*args,**kwargs)
        self.__dict__.update(kwargs)


# ----- CHECK DEFINITIONS ----- #

def is_in_guild(guild_id):
    async def predicate(ctx):
        if ctx.guild.id != guild_id:
            raise CheckFailure(message="You cannot run this command in this server.")
        else:
            return True
    return commands.check(predicate)


def is_in_skys():
    async def predicate(ctx):
        if ctx.guild.id != 609112858214793217:
            raise CheckFailure(message="You cannot run this command in this server."_
        else:
            return True
    return commands.check(predicate)


# ----- CONFIRMATION MENU ----- #

async def confirmationMenu(client, ctx, confirmationMessage=""):
    msg = await ctx.send(confirmationMessage)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author

    try:
        reaction, user = await client.wait_for('reaction_add', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send("Confirmation timed out.")
        return 0

    if user == ctx.author:
        if str(reaction) == "❌":
            return 0
        elif str(reaction) == "✅":
            return 1
    else:
        return -1

            


