import discord
from discord.ext import tasks, commands
import sys

import os

from dateutil import parser
import re

from resources.constants import *
from modules import checks
from modules.functions import *

import random
import string
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
async def add_reminder(user_id, name, time, repeat_type=0, repeat_specifiers="", until=""):
    repeat_bitstring = str(repeat_type)
    sql_insert_query = "INSERT INTO reminders VALUES (%s,%s,%s,%s)"
    data = await run_query(sql_insert_query, (name, user_id, time, repeat_bitstring), database=2)

class Reminders(commands.Cog):
    def __init__(self, client):
        self.client = client

    @tasks.loop(seconds=5.0)
    async def time_check(self):
        output = ""
        now = datetime.utcnow()
        
        data = await run_query("SELECT * FROM reminders", database=2)
        for row in data:
            if row[2] < now:
                output = (f'Your Reminder **{row[1]}** is here!')
                if row[3][0] == '0':
                    await run_query("DELETE FROM reminders WHERE name = %s AND user_id = %s", (row[0],row[1]), database=2)
                    output += '\nThis reminder will not repeat.'
                else:
                    repeat_info_string = "how did you get this, i didn't write this code yet"
                    output += 'This reminder is set to repeat {repeat_info_string}. If you\'d like to delete it, please run `hbs reminders delete <name>`.'
                user = self.client.get_user(row[1])
                await user.send(output)
        #await run_query("UPDATE vars set value = %s WHERE name = 'last_birthday'", (today.date(),))
        
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

    @commands.group()
    async def reminders(self, ctx):
        timezone = await get_timezone(ctx)
        if timezone == None:
            raise checks.OtherError("You do not currently have a timezone set. Run `hbs setTimezone <timezone>` to set a timezone.")

    @reminders.command()
    async def list(self, ctx):
        sql_get_query = "SELECT name, next_time, repeat_info FROM reminders WHERE user_id = %s"
        data = await run_query(sql_get_query, (ctx.author.id,), database=2)
        timezone = await get_timezone(ctx)
        output = ""
        for row in data:
            time = row[1].astimezone(timezone).strftime("%m/%d/%Y, %H:%M:%S")
            output += f'{row[0]} | {time} | {row[2]}\n'
        await ctx.send(output)

    @reminders.group(invoke_without_command=True)
    async def new(self, ctx, name="", *, time=""):
        reminder_id = await generate_reminder_key()
        timezone = await get_timezone(ctx)
        try:
            reminder_time = parser.parse(time)
            new_time = timezone.normalize(timezone.localize(reminder_time))
        except:
            await ctx.send("Please make sure that your command follows the format `hbs reminders new <name> <time>`.")
        
        result = await confirmationMenu(self.client, ctx, f'You would like to create a reminder named {name} at {new_time}. Is this correct? (Names with spaces must be surrounded by "" in order to parse correctly.)')
        if result == 0: await ctx.send("Operation cancelled.")
        elif result != 1: raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")
        else:
            await add_reminder(ctx.author.id, name, new_time)
            #INSERT ACTUAL CHECK SOMEWHERE
            await ctx.send(f'Reminder added! \nYou can find a list of all of your reminders by running `hbs reminders list`.')

    @new.command()
    async def repeating(self, ctx, name="", *, time=""):
        await ctx.send("This isn't implemented yet. Sorry.")
    
        
"""    async def newReminder(self, ctx, *, time=""):
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

    @commands.command(enabled=True,aliases=["addRepeatingReminder", "addRepeatReminder", "repeatingReminder", "repeatReminder", "newRepeatingReminder", "new repeat reminder", "new repeating reminder", "add repeat reminder", "add repeating reminder"])
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
"""
        
def setup(client):
    client.add_cog(Reminders(client))
