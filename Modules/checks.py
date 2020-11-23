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


# ----- CONFIRMATION MENU ----- #

async def confirmationMenu(client, ctx, confirmationMessage="",autoclear=""):
    msg = await ctx.send(confirmationMessage)
  
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author

    try:
        reaction, user = await client.wait_for('reaction_add', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send("Oops too slow!")
        if autoclear: await msg.delete()
        return 0

    if user == ctx.author:
        if str(reaction) == "❌":
            if autoclear: await msg.delete()
            return 0
        elif str(reaction) == "✅":
            if autoclear: await msg.delete()
            return 1
    else:
        if autoclear: await msg.delete()
        return -1

# ----- FIND MESSAGE VIA ID OR LINK ----- #
async def getMessage(client,ctx,id=None, channelId=None):
    if id == None:
        raise checks.InvalidArgument("Please include message ID or link.")
    elif str(id)[0:4] == "http":
        link = id.split('/')
        channel_id = int(link[6])
        msg_id = int(link[5])
        msg = await client.get_channel(channel_id).fetch_message(msg_id)
    else:
        msg = []
        for channel in ctx.guild.text_channels:
            try:
                msg.append(await channel.fetch_message(id))
            except:
                continue
            
        if msg == None:
            raise checks.InvalidArgument("That message does not exist.")
        elif len(msg) > 1:
            raise checks.InvalidArgument("Multiple messages with that ID found. Please find the correct channel ID and run the command again with the channel ID specified.")
    return msg[0]


