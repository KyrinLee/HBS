import discord
from discord.ext import commands


# ----- CHECK DEFINITIONS ----- #

def is_in_guild(guild_id):
    async def predicate(ctx):
        if ctx.guild.id != guild_id:
            raise CheckFailure("You cannot run this command in this server.")
        else:
            return True
    return commands.check(predicate)
