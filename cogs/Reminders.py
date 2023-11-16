from discord.ext import tasks, commands
import sys

from dateutil import parser

from psycopg2 import OperationalError

from resources.constants import *
from modules import checks
from modules.functions import *
from modules.reminder_functions import *

from pytz import timezone
import pytz

''' REPEAT TYPES:
    - every x (24hr, 48hr, 6hr, etc) every week is 168hr, every other week is 336hr
    - on day every month (1st of each month for example)
    - on specific weekdays (SMTWRFS)
    '''

class Reminders(commands.Cog):
    def __init__(self, client):
        self.client = client

    @tasks.loop(seconds=15.0)
    async def time_check(self):
        output = ""
        now = datetime.utcnow()
        now = now.replace(tzinfo=pytz.utc)
        
        try:
            data = await run_query("SELECT * FROM reminders")
            for row in data:
                if row[3] < now:
                    user = self.client.get_user(int(row[1]))
                    timestamp = row[3].timestamp()
                    
                    output = (f'Your Reminder **{row[2]}** is here!\n This reminder was set for <t:{timestamp}:t>')
                    if row[4] == 0:
                        await delete_reminder(row[0])
                        output += '\nThis reminder will not repeat.'
                    else:
                        repeat_info_string = "how did you get this, i didn't write this code yet"
                        output += 'This reminder is set to repeat {repeat_info_string}. If you\'d like to delete it, please run `hbs reminders delete <name>`.'

                    await user.send(output)
        except OperationalError:
            pass
        except Exception as error:
            # handle the exception
            sys.stdout.write(str(type(error).__name__))
            sys.stdout.write(str(error))
            sys.stdout.flush()


    @commands.command(pass_context=True)
    async def setTimezone(self, ctx, timezone=None):
        user_id = str(ctx.author.id)
        old_timezone = await get_timezone(user_id)
        if timezone == None:
            raise TypeError("Please include a valid timezone name!")

        if timezone in pytz.all_timezones:
            if old_timezone == None:
                await run_query("INSERT INTO timezones (user_id, timezone) VALUES (%s, %s)", (user_id, timezone))
                await ctx.send(f'Timezone {timezone} set.')
            else:
                result = await confirmationMenu(self.client, ctx, f'Would you like to replace your current timezone ({old_timezone}) with {timezone}?')
                if result == 1:
                    await run_query("UPDATE timezones SET timezone = %s WHERE user_id = %s", (timezone, user_id))
                    await ctx.send("Timezone changed.")                                  
                elif result == 0:
                    await ctx.send("Operation cancelled.")
                else:
                    raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")
        else:
            raise TypeError("Please include a valid timezone name!")\

    @commands.group()
    async def reminders(self, ctx):
        timezone = await get_timezone(ctx.author.id)
        if timezone == None:
            raise checks.OtherError("You do not currently have a timezone set. Run `hbs setTimezone <timezone>` to set a timezone.")

    @reminders.command()
    async def list(self, ctx):
        sql_get_query = "SELECT name, next_time, repeat_info FROM reminders WHERE user_id = %s"
        data = await run_query(sql_get_query, (ctx.author.id,))
        timezone = await get_timezone(ctx.author.id)
        output = ""
        for row in data:
            time = row[1].astimezone(timezone).strftime("%m/%d/%Y, %H:%M:%S")
            output += f'{row[0]} | {time} | {row[2]}\n'
        await ctx.send(output)

    @reminders.group(invoke_without_command=True)
    async def new(self, ctx, name="", *, time=""):
        reminder_id = await generate_reminder_id()
        timezone = await get_timezone(ctx.author.id)
        user_id = str(ctx.author.id)

        repeat_type = 0
        repeat_info = 0
        repeat_until = None
        
        # check for valid timezone
        if timezone == None:
            raise TypeError("You must set your timezone first! Use `hbs setTimezone <timezone>` to do so.")
        
        #parse time and add timezone info
        try:
            reminder_time = parser.parse(time)
            reminder_time = timezone.normalize(timezone.localize(reminder_time))
            reminder_timestamp = int(reminder_time.timestamp())
        except:
            raise TypeError("Please make sure that your command follows the format `hbs reminders new <name> <time>`.")
        
        result = await confirmationMenu(self.client, ctx, f'You would like to create a reminder named {name} at <t:{reminder_timestamp}:F>. Is this correct? (Names with spaces must be surrounded by "" in order to parse correctly.)')
        if result == 0: await ctx.send("Operation cancelled.")
        elif result != 1: raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")
        else:
            await add_reminder(user_id,name,reminder_time,repeat_type,repeat_info,repeat_until)
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
                raise TypeError("That was not a valid option! Please run the command again.")
            elif repeat_str[0] == 'A':
                repeat_str = repeat_str.lstrip("A ")
                try:
                    repeat_num_hours = int(repeat_str)
                except:
                    raise TypeError("That is not a valid number of hours! Please run the command again.")
                await add_reminder(ctx.author.id, new_time_utc, repeat_type=1, repeat_specifiers=repeat_num_hours)
            
            await add_reminder(ctx.author.id, new_time_utc)
"""
        
async def setup(client):
    await client.add_cog(Reminders(client))
