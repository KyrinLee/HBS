import discord
from discord.ext import commands
import sys

import os

from dateutil import parser
import re

from resources.constants import *
from modules import checks
from modules.functions import *

import aiohttp
import asyncio

from pytz import timezone
import pytz

async def get_timezone(ctx):
    timezones = await run_query("SELECT * FROM timezones WHERE id = %s", (ctx.author.id,), 1);
    if len(timezones) == 0:
        return None
    else:
        return pytz.timezone(timezones[0][1])

''' REPEAT TYPES:
    - every x (24hr, 48hr, 6hr, etc) every week is 168hr, every other week is 336hr
    - on day every month (1st of each month for example)
    - on specific weekdays (SMTWRFS)
    '''
async def add_reminder(user_id, time, repeat_type=0, repeat_specifiers="", until=""):
    pass

class Reminders(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.command(pass_context=True)
    async def setTimezone(self, ctx, timezone=None):
        old_timezone = await get_timezone(ctx)
        if timezone == None:
            raise checks.InvalidArgument("Please include a valid timezone name!")

        if timezone in pytz.all_timezones:
            if old_timezone == None:
                await run_query("INSERT INTO timezones (id, timezone) VALUES (%s, %s)", (ctx.author.id, timezone), 1)
                await ctx.send(f'Timezone {timezone} set.')
            else:
                result = await confirmationMenu(self.client, ctx, f'Would you like to replace your current timezone {old_timezone} with {timezone}?')
                if result == 1:
                    await run_query("UPDATE timezones SET timezone = %s WHERE id = %s", (timezone, ctx.author.id), 1)
                    await ctx.send("Timezone changed.")                                  
                elif result == 0:
                    await ctx.send("Operation cancelled.")
                else:
                    raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")
        else:
            raise checks.InvalidArgument("Please include a valid timezone name!")
        
    @commands.command(enabled=False, aliases=["addReminder"])
    async def newReminder(self, ctx, *, time=""):
        timezone = await get_timezone(ctx)
        if timezone == None:
            raise checks.OtherError("You do not currently have a timezone set. Run `hbs;setTimezone <timezone>` to set a timezone.")

        reminder_time = parser.parse(time)
        new_time = timezone.normalize(timezone.localize(reminder_time))
        new_time_utc = new_time.astimezone(pytz.utc)

        result = await confirmationMenu(self.client, ctx, f'You would like to create a reminder at {new_time_utc}. Is this correct?')
        if result == 0: await ctx.send("Operation cancelled.")
        elif result != 1: raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")
        else:
            await add_reminder(ctx.author.id, new_time_utc)

    @commands.command(enabled=False,aliases=["addRepeatingReminder", "addRepeatReminder", "repeatingReminder", "repeatReminder", "newRepeatingReminder", "new repeat reminder", "new repeating reminder", "add repeat reminder", "add repeating reminder"])
    async def newRepeatReminder(self, ctx, *, time=""):
        timezone = await get_timezone(ctx)
        if timezone == None:
            raise checks.OtherError("You do not currently have a timezone set. Run `hbs;setTimezone <timezone>` to set a timezone.")

        reminder_time = parser.parse(time)
        new_time = timezone.normalize(timezone.localize(reminder_time))
        new_time_utc = new_time.astimezone(pytz.utc)

        result = await confirmationMenu(self.client, ctx, f'You would like to create a reminder at {new_time}. Is this correct?')
        if result == 0: await ctx.send("Operation cancelled.")
        elif result != 1: raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")
        else:
            await ctx.send("Now please read these instructions carefully and reply with a message indicating what sort of repeat you would like your reminder to follow.\n\n"
                           "If you would like your reminder to repeat on a regular basis, such as every 24 hours, please respond with `A <number of hours>`. \n      For example, a daily repeating reminder would be `A 24`.\n"
                           "If you would like your reminder to repeat on certain day(s) every month, please respond with `B <day numbers>`.\n      For example, ia reminder on the 1st and 14th of every month would be `B 1 14`.\n"
                           "If you would like your reminder to repeat on certain weekdays every week, please respond with `C SMTWRFS`, replacing the days you do **not** want reminders on with asterisks. \n      For example, a reminder repeating every monday and friday would be `C *M***F*`. (T and R for thursday will both work.)")
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            msg = await client.wait_for('message', check=check)
            repeat_str = msg.content
            if repeat_str[0] not in ['A','B','C']:
                raise checks.InvalidArgument("That was not a valid option! Please run the command again.")
            elif repeat_str[0] == 'A':
                repeat_str = repeat_str.lstrip("A ")
                try:
                    repeat_num_hours = int(repeat_str)
                except:
                    raise checks.InvalidArgument("That is not a valid number of hours! Please run the command again.")
                await add_reminder(ctx.author.id, new_time_utc, repeat_type=1, repeat_specifiers=repeat_num_hours)
            
            await add_reminder(ctx.author.id, new_time_utc)

        
def setup(client):
    client.add_cog(Reminders(client))
