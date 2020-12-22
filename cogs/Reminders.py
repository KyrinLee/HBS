import discord
from discord.ext import commands
import sys

import os

import github
from github import Github
from dateutil import parser
import re

from resources.constants import *
from modules import checks
from modules.functions import confirmationMenu

import aiohttp
import asyncio

from pytz import timezone
import pytz

# or using an access token
g = Github(os.environ['GIST_TOKEN'])

# Then play with your Github objects:
gist = g.get_gist(os.environ['REMINDERS_GIST_ID'])

gistSem = asyncio.Semaphore(1)

class Reminders(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.command(pass_context=True)
    async def setTimezone(self, ctx, timezone=None):
        if timezone == None:
            raise checks.InvalidArgument("Please include a valid timezone name!")
        else:
            if timezone in pytz.all_timezones:
                content = gist.files["timezones.txt"].content
                if str(ctx.author.id) not in content:
                    new_content = f'{content}{str(ctx.author.id)} {timezone}\n'
                    gist.edit(files={"timezones.txt": github.InputFileContent(content=new_content)})

                else:
                    for line in content.split("\n"):
                        if str(ctx.author.id) in line:
                            timezone_info = line.replace(str(ctx.author.id), "").strip()

                    result = await confirmationMenu(self.client, ctx, f'Would you like to replace your current timezone {timezone_info} with {timezone}?')
                    if result == 1:
                        new_content = content.replace(timezone_info, timezone)
                        gist.edit(files={"timezones.txt": github.InputFileContent(content=new_content)})
                        await ctx.send("Timezone changed.")                                  
                    elif result == 0:
                        await ctx.send("Operation cancelled.")
                    else:
                        raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")
            else:
                raise checks.InvalidArgument("Please include a valid timezone name!")

    async def add_reminder(self):
        pass

        
    @commands.command(pass_context=True)
    async def newReminder(self, ctx, time="", modifiers=""):
        timezones = gist.files["timezones.txt"].content
        for line in timezones.split("\n"):
            if str(ctx.author.id) in line:
                tz = timezone(line.replace(str(ctx.author.id), "").strip())
        if tz == None:
            await ctx.send("You do not have a timezone set! Please run hbs;setTimezone <timezone> to set your timezone.")
            return

        await ctx.send(str(tz))
        reminder_time = parser.parse(time)
        new_time = tz.normalize(tz.localize(reminder_time)).astimezone(pytz.utc)

        
        
def setup(client):
    client.add_cog(Reminders(client))
