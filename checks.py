import discord
from discord.ext import commands

class InvalidArgument(commands.CommandError):
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)


# ----- CHECK DEFINITIONS ----- #

def is_in_guild(guild_id):
    async def predicate(ctx):
        if ctx.guild.id != guild_id:
            raise CheckFailure("You cannot run this command in this server.")
        else:
            return True
    return commands.check(predicate)
