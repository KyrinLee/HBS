import discord
from discord.ext import commands
from discord import Embed
import sys

import os

import asyncio
import checks
import functions
import json

import itertools
import copy
import functools
import inspect
import re
import discord.utils


class HBSHelpCommand(commands.DefaultHelpCommand):
    def __init__(self, **options):
        self.indent = options['indent']
        self.paginator = commands.Paginator(suffix=None, prefix=None)
        
        self.command_attrs = {'help', 'Shows this message.'}

        super().__init__(**options)


    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        no_category = "\u200bMiscellaneous:"
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return "" + cog.qualified_name + ':' if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Now we can add the commands to the page.
        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            self.add_indented_commands(commands, heading=category, max_size=max_size)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()


    def add_indented_commands(self, commands, *, heading, max_size=None):
        
        if not commands:
            return

        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(commands)

        get_width = discord.utils._string_width
        for command in commands:
            name = command.name
            entry = '{0}{1: <24} {2}'.format(self.indent * ' ', name, command.short_doc)
            self.paginator.add_line(self.shorten_text(entry))


    async def send_cog_help(self, cog):
        bot = self.context.bot
        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        self.paginator.add_line(f'**{cog}**', empty=True)

        if cog.description:
            self.paginator.add_line(cog.description, empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        if filtered:
            self.paginator.add_line('**%s %s**' % (cog.qualified_name, self.commands_heading))
            for command in filtered:
                self.paginator.add_line(f'{command.name}')

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()


    async def send_group_help(self, group):
        """|coro|
        Handles the implementation of the group page in the help command.
        This function is called when the help command is called with a group as the argument.
        It should be noted that this method does not return anything -- rather the
        actual message sending should be done inside this method. Well behaved subclasses
        should use :meth:`get_destination` to know where to send, as this is a customisation
        point for other users.
        You can override this method to customise the behaviour.
        .. note::
            You can access the invocation context with :attr:`HelpCommand.context`.
            To get the commands that belong to this group without aliases see
            :attr:`Group.commands`. The commands returned not filtered. To do the
            filtering you will have to call :meth:`filter_commands` yourself.
        Parameters
        -----------
        group: :class:`Group`
            The group that was requested for help.
        """
        return None

    async def send_command_help(self, command):
        """|coro|
        Handles the implementation of the single command page in the help command.
        It should be noted that this method does not return anything -- rather the
        actual message sending should be done inside this method. Well behaved subclasses
        should use :meth:`get_destination` to know where to send, as this is a customisation
        point for other users.
        You can override this method to customise the behaviour.
        .. note::
            You can access the invocation context with :attr:`HelpCommand.context`.
        .. admonition:: Showing Help
            :class: helpful
            There are certain attributes and methods that are helpful for a help command
            to show such as the following:
            - :attr:`Command.help`
            - :attr:`Command.brief`
            - :attr:`Command.short_doc`
            - :attr:`Command.description`
            - :meth:`get_command_signature`
            There are more than just these attributes but feel free to play around with
            these to help you get started to get the output that you want.
        Parameters
        -----------
        command: :class:`Command`
            The command that was requested for help.
        """
        return None

    


    
