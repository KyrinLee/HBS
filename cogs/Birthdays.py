import discord
from discord.ext import tasks, commands
import sys
import os

import github
from github import Github
from dateutil import parser
import re

from modules import checks, pk, birthday_functions
from modules.Birthday import Birthday

from modules.birthday_functions import *
from modules.functions import *
from resources.constants import *

from datetime import datetime, date
import time

import aiohttp, asyncio

class Birthdays(commands.Cog):
    def __init__(self, client):
        self.client = client

    @tasks.loop(seconds=30.0)
    async def time_check(self):
        output = ""
        birthdays = []
        today = get_today()
        
        data = await run_query("SELECT * FROM vars WHERE name = 'last_birthday'")
        
        last_birthday_string = "0000-00-00" if len(data[0]) == 0 else data[0][1]
        last_birthday = parser.parse(last_birthday_string).date()

        if today.date() != last_birthday:
            birthdays.append(await get_pk_birthdays_by_day(today))
            birthdays.append(await get_manual_birthdays_by_day(today))

            output = await format_birthdays_day(birthdays, today, self.client)
            await split_and_send(output, self.client.get_channel(HBS_CHANNEL_ID))
                
            await run_query("UPDATE vars set value = %s WHERE name = 'last_birthday'", (today.date(),))

    @tasks.loop(seconds=1800)
    async def update_cache(self):
<<<<<<< HEAD
        birthday_functions.pluralkit_cache = await get_all_pk_birthdays()
        birthday_functions.manual_cache = await get_manual_birthdays()
=======
        birthday_functions.pluralkit_birthdays_cached_dict = await get_pk_birthdays()
>>>>>>> parent of 6666218 (update birthdays)
        
    ''' ------------------------------
            GETTING BIRTHDAYS
        ------------------------------'''
        
    @commands.command(brief="See all of today's birthdays.")
    async def todaysBirthdays(self, ctx):
        async with ctx.channel.typing():
            today = get_today()
        
            birthdays = await get_pk_birthdays_by_day(today)
            birthdays += await get_manual_birthdays_by_day(today)

            output = await format_birthdays_day(birthdays, today, self.client)
            await split_and_send(output, ctx.channel)

    @commands.command(aliases=["birthdays"], brief="See all of a given day's birthdays.")
    async def daysBirthdays(self, ctx, *, day=None):
        async with ctx.channel.typing():
            day = get_today() if day.lower() == "today" else parser.parse(day)
                
            birthdays = await get_pk_birthdays_by_day(day)
            birthdays += await get_manual_birthdays_by_day(day)

            output = await format_birthdays_day(birthdays, day, self.client)
            await split_and_send(output, ctx.channel)

    @commands.command(brief="See all birthdays within the next week.")
    async def upcomingBirthdays(self, ctx, num_days=7):
        async with ctx.channel.typing():
            output = "**Upcoming Birthdays:**\n"
            start_day = get_today() + timedelta(days=1)
            end_day = start_day + timedelta(days=num_days-1)

            birthdays = await get_pk_birthdays_by_date_range(start_day, end_day)
            birthdays += await get_manual_birthdays_by_date_range(start_day, end_day)
            
            for i in range(0,num_days+1):
                day = start_day + timedelta(days=i)
                days_birthdays = [b for b in birthdays if b.same_day_as(day)]
                sys.stdout.write(str(days_birthdays) + "\n")
                
                text = await format_birthdays_day(days_birthdays, day, self.client, header_format="")
                if text != "":
                    output += f'__{re.sub("x","",re.sub("x0","",day.strftime("%B x%d")))}__\n{text}\n'

        await split_and_send(output, ctx.channel)

    @commands.command(aliases=["myBirthdays", "birthdayList","birthdaysList"], brief="See all of your birthdays.")
    async def listBirthdays(self, ctx):
        async with ctx.channel.typing():
            system = await pk.get_system_by_discord_id(ctx.author.id)

            output = "**My Birthdays:**\n"
            birthdays = await get_pk_birthdays_by_system(system.hid)
            birthdays += await get_manual_birthdays_by_user(ctx.author.id)
            
            output += await format_birthdays_year(birthdays)
        await split_and_send(output, ctx.channel)

    @commands.command(brief="See all birthdays, from all users.")
    @checks.is_vriska()
    async def listAllBirthdays(self, ctx):
        birthdays = []
        async with ctx.channel.typing():
            output = "**All Birthdays:**\n"
            
            birthdays += await get_all_pk_birthdays()
            birthdays += await get_manual_birthdays()

            output += await format_birthdays_year(birthdays)
        await split_and_send(output, ctx.channel)

    @commands.command(aliases=["listSysBirthdays","listPKBirthdays","mySysBirthdays","mySystemBirthdays","myPKBirthdays"], brief="List all birthdays in your PluralKit System.")
    async def listSystemBirthdays(self, ctx):
        async with ctx.channel.typing():
            system = await pk.get_system_by_discord_id(ctx.author.id)
            output = "**My PluralKit Birthdays:**\n"

            birthdays = await get_pk_birthdays_by_system(system.hid)
            
            output += await format_birthdays_year(birthdays)
        await split_and_send(output, ctx.channel)

    @commands.command(brief="List all birthdays you have manually added.")
    async def listManualBirthdays(self, ctx):
        output = "**My Manual Birthdays:**\n"
        async with ctx.channel.typing():
            birthdays = await get_manual_birthdays_by_user(ctx.author.id)
            if len(birthdays) == 0:
                raise checks.OtherError(NO_MANUAL_BIRTHDAYS_SET)

            output += await format_birthdays_year(birthdays)
        await split_and_send(output, ctx.channel)

    ''' ------------------------------
             MANUAL BIRTHDAYS
        ------------------------------'''

    @commands.command(brief="Add a manual birthday.")
    async def addBirthday(self, ctx, name="", *,birthday_raw=""):
        new_birthday = Birthday.from_raw(name.capitalize(), birthday_raw, ctx.author.id)
        
        async with ctx.channel.typing():
            birthday_conflict = await get_manual_birthday_by_user_and_name(name.capitalize(), ctx.author.id)
            if birthday_conflict != None:
                await ctx.send(f'You already have a birthday named {new_birthday.name}!')
                await ctx.invoke(self.client.get_command('updateBirthday'), name=name, birthday_raw=birthday_raw)
                return
            
            await add_manual_birthday(new_birthday)
        
        await ctx.send(f'Birthday {new_birthday.short_birthday()} set for {new_birthday.name}.')

    @commands.command(brief="Update a manual birthday.")
    async def updateBirthday(self, ctx, name="", *,birthday_raw=""):
        new_birthday = Birthday.from_raw(name.capitalize(), birthday_raw, ctx.author.id)
        birthday_conflict = await get_manual_birthday_by_user_and_name(name.capitalize(), ctx.author.id)
        
        if birthday_conflict != None:
            menu_text = f' Would you like to replace the birthday for {name.capitalize()} on {birthday_conflict.short_birthday()} with {new_birthday.short_birthday()}?'
            result = await confirmationMenu(self.client, ctx, menu_text)
            if result == 1:
                await update_manual_birthday(new_birthday)
                await ctx.send(f'Birthday for {new_birthday.name} updated to {new_birthday.short_birthday()}.')
                return 
            elif result == 0:
                await ctx.send("Operation cancelled.")
                return
            else:
                raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")

        await ctx.send(f'Birthday {new_birthday.short_birthday()} set for {new_birthday.name}.')

    @commands.command(aliases=["deleteBirthday","delBirthday"],brief="Remove a manual birthday.")
    async def removeBirthday(self, ctx, name=""):
        async with ctx.channel.typing():
            await remove_manual_birthday(name, ctx.author.id)
        await ctx.send(f'Birthday removed.')
    
    ''' ------------------------------
            SYSTEM BIRTHDAYS
        ------------------------------'''

    @commands.command(brief="Connect your PluralKit account.")
    async def addSystemBirthdays(self, ctx):
        async with ctx.channel.typing():
            sql_insert_query = """ INSERT INTO pkinfo (id, token, show_age) VALUES (%s,%s,False)"""
            token = ""
            system = await pk.get_system_by_discord_id(ctx.author.id)
            data = await run_query("SELECT * FROM pkinfo")
            
            if len(data) > 0:
                for i in data:
                    if i[0] == str(system.hid):
                        raise checks.OtherError("Your PluralKit account is already connected!")
            try:
                async with aiohttp.ClientSession() as session:
                    members = await system.members(session)
            except:
                await ctx.send(NO_ACCESS + "\nPlease check your DMs!")
                token = await pk.prompt_for_pk_token(self.client, ctx)

            record_to_insert = (str(system.hid), token)
            await run_query(sql_insert_query, record_to_insert)

        await ctx.send("PluralKit Birthdays successfully connected!")   

    @commands.command(brief="Disconnect your PluralKit account.")
    async def deleteSystemBirthdays(self, ctx):
        async with ctx.channel.typing():
            sql_delete_query = """DELETE FROM pkinfo WHERE id = %s"""
            system = await pk.get_system_by_discord_id(ctx.author.id)

            data = await run_query("SELECT * FROM pkinfo")
            currently_connected = False
            
            if len(data) > 0:
                for i in data:
                    if i[0] == str(system.hid):
                        currently_connected = True
                        
            if currently_connected:
                record = (str(system.hid),)
                await run_query(sql_delete_query, record)
                await ctx.send("PluralKit account disconnected.")

            else:
                raise checks.OtherError("Your PluralKit account is already unconnected.")
            
    @commands.command(aliases=["addtoken","pktoken"],brief="Add a token to your PluralKit connection.")
    async def addPKToken(self, ctx):
        async with ctx.channel.typing():
            system = await pk.get_system_by_discord_id(ctx.author.id)
            token = await pk.prompt_for_pk_token(self.client, ctx)
            
            sql_update_query = "UPDATE pkinfo SET token = %s WHERE id = %s"
            record_to_insert = (token, str(system.hid))
            await run_query(sql_update_query, record_to_insert)

        await ctx.send("PluralKit Token successfully added!")

    @commands.command(brief="Set your system birthdays to show ages based on birth year.")
    async def showAge(self, ctx):
        async with ctx.channel.typing():
            system = await pk.get_system_by_discord_id(ctx.author.id)
            sql_update_query = "UPDATE pkinfo SET show_age = True WHERE id = %s"
            record_to_insert = (str(system.hid),)
            await run_query(sql_update_query, record_to_insert)

        await ctx.send("Your PluralKit birthdays will now show age based on birth year.")

    @commands.command(brief="Set your system birthdays to hide ages based on birth year.")
    async def hideAge(self, ctx):
        async with ctx.channel.typing():
            system = await pk.get_system_by_discord_id(ctx.author.id)
            sql_update_query = "UPDATE pkinfo SET show_age = False WHERE id = %s"
            record_to_insert = (str(system.hid),)
            await run_query(sql_update_query, record_to_insert)

        await ctx.send("Your PluralKit birthdays will no longer show age based on birth year.")
    
def setup(client):
    client.add_cog(Birthdays(client))
