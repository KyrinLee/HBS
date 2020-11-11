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

class HBSCommand(commands.DefaultHelpCommand):
    def __init__(self, **options):
        self.indent = options['indent']
        self.paginator = commands.Paginator(suffix=None, prefix=None)
        
        self.command_attrs = {'help', 'Shows this message'}

        super().__init__(**options)


    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        no_category = '\u200b{0.no_category}:'.format(self)
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

    
