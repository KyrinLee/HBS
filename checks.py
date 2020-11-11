import discord
from discord.ext import commands

import asyncio

class InvalidArgument(commands.CommandError):
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




# ----- CONFIRMATION MENU ----- #

async def confirmationMenu(ctx, confirmationMessage):
    msg = await ctx.send(confirmationMessage)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return user == message.author and str(reaction.emoji) == '👍'

    try:
        reaction, user = await bot.wait_for('reaction_add', check=check, timeout=60.0)
    except:
        ctx.send("Confirmation timed out.")
        return 0
    else:
        if reaction == '❌':
            await ctx.send("Cancelled.")
            return 0
        elif reaction == '✅':
            await ctx.send("Confirmed.")
            return 1

    return -1
            


