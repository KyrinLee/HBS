import discord
from discord.ext import tasks, commands
import sys
import os

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

class Birthdays(commands.Cog, name="Birthday Commands"):
    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        if not ctx.guild.id == SKYS_SERVER_ID and not ctx.author.id == VRISKA_ID:
            raise checks.WrongServer()
        return True

    @tasks.loop(seconds=30.0)
    async def time_check(self):
        output = ""
        birthdays = []
        today = get_today()
        
        data = await run_query("SELECT * FROM vars WHERE name = 'last_birthday'")
        
        last_birthday_string = "0000-00-00" if len(data[0]) == 0 else data[0][1]
        last_birthday = parser.parse(last_birthday_string).date()

        if today.date() != last_birthday:
            birthdays = await get_pk_birthdays_by_day(today)
            birthdays += await get_manual_birthdays_by_day(today)

            output = await format_birthdays_day(birthdays, today, self.client)
            await split_and_send(output, self.client.get_channel(HBS_CHANNEL_ID))
                
            await run_query("UPDATE vars set value = %s WHERE name = 'last_birthday'", (today.date(),))
        
    ''' ------------------------------
            GETTING BIRTHDAYS
        ------------------------------'''

    @commands.group(invoke_without_command=True, brief="See all of a day's birthdays.", aliases=["birthday"])
    async def birthdays(self, ctx, *, day=None):
        async with ctx.channel.typing():
            if day!=None:
                try:
                    day = parser.parse(day)
                except:
                    raise discord.InvalidArgument("Invalid date or command.")
            
            try:
                birthdays = await get_pk_birthdays_by_day(day)
                birthdays += await get_manual_birthdays_by_day(day)

                output = await format_birthdays_day(birthdays, day, self.client)
                await split_and_send(output, ctx.channel)
            except:
                raise discord.InvalidArgument("Invalid date or command.")

    @birthdays.command(brief="See all of today's birthdays.")
    async def today(self, ctx):
        async with ctx.channel.typing():
            today = get_today()
        
            birthdays = await get_pk_birthdays_by_day(today)
            birthdays += await get_manual_birthdays_by_day(today)

            output = await format_birthdays_day(birthdays, today, self.client)
        await split_and_send(output, ctx.channel)

    @birthdays.command(brief="See all birthdays within the next week.")
    @checks.is_in_skys()
    async def upcoming(self, ctx, num_days=7):
        async with ctx.channel.typing():
            output = "**__Upcoming Birthdays:__**\n"
            start_day = get_today() + timedelta(days=1)
            end_day = start_day + timedelta(days=num_days)

            birthdays = await get_pk_birthdays_by_date_range(start_day, end_day)
            birthdays += await get_manual_birthdays_by_date_range(start_day, end_day)
            
            for i in range(0,num_days):
                day = start_day + timedelta(days=i)
                days_birthdays = [b for b in birthdays if b.same_day_as(day)]
                
                if days_birthdays != []:
                    output += await format_birthdays_day(days_birthdays, day, self.client)

        await split_and_send(output, ctx.channel)

    @birthdays.command(brief="See all of your birthdays.")
    async def list(self, ctx, *, flags=""):
        async with ctx.channel.typing():
            if "-m" in flags and "-s" in flags:
                flags = ""
            system = await pk.get_system_by_discord_id(ctx.author.id)

            output = "**My Birthdays:**\n"
            birthdays = []
            if ("-m" not in flags):
                birthdays += await get_pk_birthdays_by_system(system.hid)
            if ("-s" not in flags):
                birthdays += await get_manual_birthdays_by_user(ctx.author.id)
            
            output += await format_birthdays_year(birthdays)
            if "-m" in flags: output += "\n(Showing only manual birthdays.)"
            if "-s" in flags: output += "\n(Showing only system birthdays.)"
        await split_and_send(output, ctx.channel)
        
    ''' ------------------------------
             MANUAL BIRTHDAYS
        ------------------------------'''

    @birthdays.command(brief="Add a manual birthday.", aliases=["new","n"])
    async def add(self, ctx, name="", *,birthday_raw=""):
        if (name in range(1,32) or name.lower() in ["january","jan","february","feb","march","mar","april","apr","may","june","jun","july","jul","august","aug","september","sep","sept","october","oct","november","nov","december","dec"]):
            await confirmationMenu(self.client, ctx, f'You have entered {name} as the name for this birthday. Is this correct?')           

        new_birthday = Birthday.from_raw(name.capitalize(), birthday_raw, ctx.author.id)
        
        async with ctx.channel.typing():
            birthday_conflict = await get_manual_birthday_by_user_and_name(name.capitalize(), ctx.author.id)
            if birthday_conflict != None:
                await ctx.send(f'You already have a birthday named {new_birthday.name}!')
                await ctx.invoke(self.client.get_command('updateBirthday'), name=name, birthday_raw=birthday_raw)
                return
            
            await add_manual_birthday(new_birthday)
        
        await ctx.send(f'Birthday {new_birthday.short_birthday()} set for {new_birthday.name}.')
        
    @birthdays.command(brief="Update a manual birthday.", aliases=["edit"])
    async def update(self, ctx, name="", *,birthday_raw=""):
        new_birthday = Birthday.from_raw(name.capitalize(), birthday_raw, ctx.author.id)
        birthday_conflict = await get_manual_birthday_by_user_and_name(name.capitalize(), ctx.author.id)
        
        if birthday_conflict != None:
            menu_text = f' Would you like to replace the birthday for {name.capitalize()} on {birthday_conflict.short_birthday()} with {new_birthday.short_birthday()}?'
            result = await confirmationMenu(self.client, ctx, menu_text)
            if result == 1:
                await update_manual_birthday(new_birthday)
                await ctx.send(f'Birthday for {new_birthday.name} updated to {new_birthday.short_birthday()}.')
                return 

        await ctx.send(f'Birthday {new_birthday.short_birthday()} set for {new_birthday.name}.')

    @birthdays.command(aliases=["remove", "rem"],brief="Remove a manual birthday.")
    async def delete(self, ctx, name=""):
        async with ctx.channel.typing():
            await delete_manual_birthday(name, ctx.author.id)
        await ctx.send(f'Birthday removed. Probably. Vriska is too dumb to figure out how to check if a birthday was actually removed so you should double check with `hbs birthdays list -m`. If it wasn\'t removed make sure you capitalized right cause this is case sensitive for some reason. Thanks! ::::)')
        
    ''' ------------------------------
            SYSTEM BIRTHDAYS
        ------------------------------'''

    @birthdays.command(brief="Connect your PluralKit account.")
    async def connect(self, ctx):
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

    @birthdays.command(brief="Disconnect your PluralKit account.")
    async def disconnect(self, ctx):
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
            
    @birthdays.command(aliases=["addtoken","pktoken"],brief="Add a token to your PluralKit connection.")
    async def token(self, ctx):
        async with ctx.channel.typing():
            system = await pk.get_system_by_discord_id(ctx.author.id)
            token = await pk.prompt_for_pk_token(self.client, ctx)
            
            sql_update_query = "UPDATE pkinfo SET token = %s WHERE id = %s"
            record_to_insert = (token, str(system.hid))
            await run_query(sql_update_query, record_to_insert)

        await ctx.send("PluralKit Token successfully added!")

    @birthdays.group(invoke_without_command=True)
    async def age(self, ctx):
        async with ctx.channel.typing():
            system = await pk.get_system_by_discord_id(ctx.author.id)
            sql_get_query = "SELECT show_age FROM pkinfo WHERE id = %s"
            data = await run_query(sql_get_query, (str(system.hid),))
        if (data[0][0]):
            await ctx.send(f'Your PluralKit birthday ages are currently shown.')
        else:
            await ctx.send(f'Your PluralKit birthdays ages are currently hidden.')

    @age.command(brief="Set your system birthdays to show ages based on birth year.", aliases=["enable","on"])
    async def show(self, ctx):
        async with ctx.channel.typing():
            system = await pk.get_system_by_discord_id(ctx.author.id)
            sql_update_query = "UPDATE pkinfo SET show_age = True WHERE id = %s"
            record_to_insert = (str(system.hid),)
            await run_query(sql_update_query, record_to_insert)

        await ctx.send("Your PluralKit birthdays will now show age based on birth year.")

    @age.command(brief="Set your system birthdays to hide ages based on birth year.", aliases=["disable","off"])
    async def hide(self, ctx):
        async with ctx.channel.typing():
            system = await pk.get_system_by_discord_id(ctx.author.id)
            sql_update_query = "UPDATE pkinfo SET show_age = False WHERE id = %s"
            record_to_insert = (str(system.hid),)
            await run_query(sql_update_query, record_to_insert)

        await ctx.send("Your PluralKit birthdays will no longer show age based on birth year.")

    @birthdays.command(brief="See all birthdays, from all users.", enabled=False)
    @checks.is_vriska()
    async def listall(self, ctx):
        birthdays = []
        async with ctx.channel.typing():
            output = "**All Birthdays:**\n"
            
            birthdays += await get_all_pk_birthdays()
            birthdays += await get_manual_birthdays()

            output += await format_birthdays_year(birthdays)
        await split_and_send(output, ctx.channel)
    
def setup(client):
    client.add_cog(Birthdays(client))
