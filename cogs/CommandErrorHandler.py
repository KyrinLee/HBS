import discord
import traceback
import sys
from discord.ext import commands

import random

from modules import checks
from resources.constants import *

from modules.pk import CouldNotConnectToPKAPI

class CommandErrorHandler(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = ()

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        elif isinstance(error, commands.CommandNotFound):
            message = ctx.message
            message_content = message.content.lower().lstrip("hbs").lstrip(";").lstrip()
            if message.webhook_id == None:
                    if message_content.startswith(("do","are", "is","did")):
                        if all([any(i in message_content for i in ["hussie","cowardbot"]), any(k in message_content for k in ["love","like","hate","kismesis","kismeses","date","dating"])]):
                            await asyncio.sleep(1)
                            await message.channel.send("Yes! " + str(blobspade))
                            return
                        else:
                            await asyncio.sleep(1)
                            await message.channel.send(random.choice(["Yes!","No.","Maybe!"]))
                            return
                        
                    elif message_content.startswith("when"):
                        if any(s in message_content for s in ["wedding","marry","married"]):
                            await asyncio.sleep(1)
                            await message.channel.send("Not soon enough! " + str(blobspade))
                            return
                        else:
                            await asyncio.sleep(1)
                            start_date = date.today()
                            end_date = date(2500, 12, 31)
                        
                            random_number_of_days = random.randrange(((end_date-start_date).days))
                            random_date = start_date + timedelta(days=random_number_of_days)
                            await message.channel.send(random_date.strftime("%B %m, %Y").replace(' 0',' '))
                            return
                    else:
                        await ctx.send("I don't think that's a real command. Try `hbs;help` for a list of commands.")
            else:
                await ctx.send("I don't think that's a real command. Try `hbs;help` for a list of commands.")

        elif isinstance(error, commands.DisabledCommand):
            await ctx.send(f'You cannot use this command! {ctx.command.capitalize()} is currently disabled.')

        elif isinstance(error, commands.CheckFailure):
            if isinstance(error, commands.NotOwner):
                output = "Stop tryna run commands you don't have permissions for! <:angercry:757731437326762014>"
            elif isinstance(error, checks.NoDMs):
                output = "You can't run this command in DMs!"
            elif isinstance(error, checks.WrongServer):
                output = "You can't run that command in this server!"
            else:
                output = error
                
            await ctx.send(output)

        elif isinstance(error, checks.FuckyError):
            await ctx.send("Something went fucky here! Ping Vriska, she won't know what the problem is either but it'll at least be funny." + str(error))

        elif isinstance(error, discord.InvalidArgument):
            await ctx.send(error)

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(error)
            
        elif isinstance(error, discord.HTTPException):
            if error.code == 50035:
                await ctx.send("I tried to send a message longer than 2000 characters! I probably shouldn't be doing that.")

        elif isinstance(error, CouldNotConnectToPKAPI):
            await self.client.get_channel(HBS_CHANNEL_ID).send("PK has been API banned! @ramblingArachnid#8781 you should make HBS turn on tupper when this happens")
            
        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            await ctx.send("I did a fucky.")
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            print(str(ctx))


def setup(client):
    client.add_cog(CommandErrorHandler(client))
