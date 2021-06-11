import discord
from discord.ext import commands
from discord import Embed
import sys

import os

import asyncio
import json

import itertools
import copy
import functools
import inspect
import re
import discord.utils


from modules import checks, functions
from resources.constants import *

newline = "\n"

class HelpMenu():
    def __init__(self, bot, pages = []):
        self.bot = bot
        self.pages = pages
        self.current_page = 0
        self.max_page = len(pages) - 1
        self.message_id = None
        self.message = None

    @classmethod
    async def create(cls, ctx, bot, pages):
        menu = HelpMenu(bot,pages)
        await menu.create_help_message(ctx)
        return menu

    async def create_help_message(self,ctx):
        embed = Embed.from_dict(self.pages[self.current_page])
        embed.set_author(name=f'HBS Help (Page {self.current_page+1} of {self.max_page+1})')
        msg = await ctx.send(content=" ", embed=embed)
        await msg.add_reaction(left_arrow)
        await msg.add_reaction(right_arrow)
        self.message = msg

    async def next_page(self):
        if self.current_page < self.max_page:
            self.current_page += 1;
        else:
            self.current_page = 0;
        await self.update_embed()
        
    async def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1;
        else:
            self.current_page = self.max_page;
        await self.update_embed()

    async def update_embed(self):
        embed = Embed.from_dict(self.pages[self.current_page])
        embed.set_author(name=f'HBS Help (Page {self.current_page+1} of {self.max_page+1})')
        await self.message.edit(embed=embed)
    

class HBSHelpCommand(commands.DefaultHelpCommand):
    def __init__(self, **options):
        self.indent = options['indent']
        self.paginator = commands.Paginator(suffix=None, prefix=None)
        
        self.command_attrs = {'help', 'Shows this message.'}

        super().__init__(**options)

    async def send_bot_help(self, mapping):
        pages = []
        categories = []

        ctx = self.context
        bot = ctx.bot

        no_category = "\u200bMiscellaneous"
        def get_category(command, *, no_category=no_category):
            cog = command.cog
            return cog.qualified_name if cog is not None else no_category

        filtered = await self.filter_commands(bot.commands, sort=True, key=get_category)
        max_size = self.get_max_size(filtered)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Now we can add the commands to the page.
        for category, commands in to_iterate:
            commands = sorted(commands, key=lambda c: c.name) if self.sort_commands else list(commands)
            categories.append(category)
            pages.append(self.format_page(commands, heading=category, max_size=max_size))

        pages.insert(0, self.format_menu_page(categories))

        #sys.stdout.write(str(pages))

        menu = await HelpMenu.create(ctx, bot, pages)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in [left_arrow,right_arrow]

        timeout = False
        while timeout == False:
            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=300.0, check=check)
            except asyncio.TimeoutError:
                await menu.message.clear_reactions()
                timeout = True
            else:
                if str(reaction.emoji) == left_arrow:
                    await menu.previous_page()
                elif str(reaction.emoji) == right_arrow:
                    await menu.next_page()

    def format_menu_page(self, categories, *, max_size=None):
        
        if not categories:
            return
        output = ""

        page = {}
        #page['title'] = "Categories"
        page['description'] = ""
        page['color']= 0x005682
        page['type'] = "rich"
        page['fields'] = []

        for category in categories:
            output += category + "\n"

        page['fields'].append({'name':'Categories','value':output})

        return page
      
        
    def format_page(self, commands, *, heading, max_size=None):
        
        if not commands:
            return

        page = {}
        page['title'] = heading
        page['description'] = ""
        page['color']= 0x005682
        page['type'] = "rich"
        page['fields'] = []

        get_width = discord.utils._string_width
        for command in commands:
            command_help = "\u200b" if command.short_doc in [None,""] else command.short_doc
            page['fields'].append({'name':command.name,'value':command_help})

        return page


    async def send_cog_help(self, cog):
        bot = self.context.bot
        if bot.description:
            self.paginator.add_line(bot.description, empty=True)

        self.paginator.add_line(f'{cog.qualified_name}:', empty=True)

        if cog.description:
            self.paginator.add_line(cog.description, empty=True)

        filtered = await self.filter_commands(cog.get_commands(), sort=self.sort_commands)
        if filtered:
            for command in filtered:
                self.paginator.add_line(f'{command.name}')

            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    async def send_command_help(self, command):
        bot = self.context.bot
        if bot.description:
            self.paginator.add_line(bot.description, empty=True)
            
        with open('resources/HelpMenu.json') as f:
            data = json.load(f)

        prefix = bot.command_prefix[0]
        
        aliases = [command.name]
        aliases = aliases + command.aliases
        
        command_data = data.pop(command.name,{})
        
        signature = command_data.get('signature',"") or command.signature
        #REPLACE [animated] for [-s|-a]
        signature = signature.replace("[animated]","[static|s|animated|a]")
        signature = signature.replace("[starboard=starboard]","[starboard]")
        signature = signature.replace("[mobile]","[-m]")
        signature = signature.replace("[messageIDorLink]","<Message ID/Link>")
        
        additional_help = command_data.get('additional_help',"")
        if additional_help == "":
            if command.brief != None and command.help != None:
                additional_help = command.brief + "\n" + command.help
            else:
                additional_help = command.brief or command.help
            
        lines_to_add = []
        max_command_length = 0

        lines_to_add = [(prefix + str(a)) for a in aliases]
        max_command_length = len(max(lines_to_add, key = len)) 

        for line in lines_to_add:
            self.paginator.add_line(line.ljust(max_command_length + 1) + signature)
            
        self.paginator.add_line(newline + additional_help)
        
        await self.send_pages()

    async def command_callback(self, ctx, *, command=None):
        
        await self.prepare_help_command(ctx, command)
        bot = ctx.bot

        if command is None:
            mapping = self.get_bot_mapping()
            return await self.send_bot_help(mapping)

        # Check if it's a cog
        cog = bot.get_cog(command)
        if cog is not None:
            return await self.send_cog_help(cog)

        maybe_coro = discord.utils.maybe_coroutine

        # If it's not a cog then it's a command.
        # Since we want to have detailed errors when someone
        # passes an invalid subcommand, we need to walk through
        # the command group chain ourselves.
        keys = command.split(' ')
        cmd = bot.all_commands.get(keys[0])
        if cmd is None:
            string = await maybe_coro(self.command_not_found, self.remove_mentions(keys[0]))
            return await self.send_error_message(string)

        for key in keys[1:]:
            try:
                found = cmd.all_commands.get(key)
            except AttributeError:
                string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                return await self.send_error_message(string)
            else:
                if found is None:
                    string = await maybe_coro(self.subcommand_not_found, cmd, self.remove_mentions(key))
                    return await self.send_error_message(string)
                cmd = found

        return await self.send_command_help(cmd)
        

    
    '''async def send_bot_help(self, mapping):
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
    
        self.paginator.add_line(heading)
        max_size = max_size or self.get_max_size(commands)

        get_width = discord.utils._string_width
        for command in commands:
            name = command.name
            #entry = '{0}{1: <18} {2}'.format(self.indent * ' ', name, command.short_doc)
            entry = '{0}{1}: {2}'.format(self.indent * ' ', name, command.short_doc)
            #self.paginator.add_line(self.shorten_text(entry))

        return entry'''

    
