import discord
import traceback
import sys
from discord.ext import commands

import checks

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

        ignored = (commands.CommandNotFound, )

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f'You cannot use this command! {ctx.command.capitalize()} is currently disabled.')

        elif isinstance(error, commands.CheckFailure):
            output = "You did a fucky. "
            if isinstance(error, commands.NotOwner):
                output += "Stop tryna run commands you don't have permissions for! <:angercry:757731437326762014>"
            else:
                output += str(error)
                
            await ctx.send(output)

        elif isinstance(error, checks.FuckyError):
            await ctx.send("Something went fucky here! Ping Vriska, she won't know what the problem is either but it'll at least be funny." + str(error))

        elif isinstance(error, checks.InvalidArgument):
            await ctx.send(error)

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(error)
            
        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            await ctx.send("I did a fucky.")
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def setup(client):
    client.add_cog(CommandErrorHandler(client))
