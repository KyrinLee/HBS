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

import aiohttp, asyncio

class Birthdays(commands.Cog):
    def __init__(self, client):
        self.client = client

    @tasks.loop(seconds=30.0)
    async def time_check(self):
        output = ""
        birthdays = []
        conn,cursor = database_connect()
        today = get_today()
        
        cursor.execute("SELECT * FROM vars WHERE name = 'last_birthday'")
        data = cursor.fetchall()
        last_birthday_string = "0000-00-00" if len(data[0]) == 0 else data[0][1]
        last_birthday = parser.parse(last_birthday_string).date()

        if today.date() != last_birthday:
            birthdays = await get_pk_birthdays_by_day(today)
            birthdays.update(await get_gist_birthdays_by_day(today))

            output = await format_birthdays_day(birthdays, day, self.client)
            await split_and_send(output, self.client.get_channel(HBS_CHANNEL_ID))
                
            cursor.execute("UPDATE vars set value = %s WHERE name = 'last_birthday'", (today.date(),))

        database_disconnect(conn,cursor)

    @tasks.loop(seconds=3600)
    async def update_cache(self):
        birthday_functions.pluralkit_birthdays_cached_dict = await get_pk_birthdays()
        birthday_functions.gist_birthdays_cached_dict = await get_gist_birthdays()
        
    ''' ------------------------------
            GETTING BIRTHDAYS
        ------------------------------'''
        
    @commands.command(brief="See all of today's birthdays.")
    async def todaysBirthdays(self, ctx):
        async with ctx.channel.typing():
            today = get_today()
        
            birthdays = await get_pk_birthdays_by_day(today)
            birthdays.update(await get_gist_birthdays_by_day(today))

            output = await format_birthdays_day(birthdays, today, self.client)
            output = replace_user_ids_with_nicknames(self.client,output)
            await split_and_send(output, ctx.channel)

    @commands.command(aliases=["birthdays"], brief="See all of a given day's birthdays.")
    async def daysBirthdays(self, ctx, *, day=None):
        async with ctx.channel.typing():
            day = get_today() if day.lower() == "today" else parser.parse(day)
                
            birthdays = await get_pk_birthdays_by_day(day)
            birthdays.update(await get_gist_birthdays_by_day(day))

            output = await format_birthdays_day(birthdays, day, self.client)
            output = replace_user_ids_with_nicknames(self.client,output)
            await split_and_send(output, ctx.channel)

    @commands.command(brief="See all birthdays within the next week.")
    async def upcomingBirthdays(self, ctx):
        async with ctx.channel.typing():
            num_days = 7
            output = "**Upcoming Birthdays:**\n"
            start_day = get_today() + timedelta(days=1)
            end_day = start_day + timedelta(days=num_days-1)

            pk_birthdays = await get_pk_birthdays_by_date_range(start_day, end_day)
            gist_birthdays = await get_gist_birthdays_by_date_range(start_day, end_day)

            for i in range(0,num_days):
                pk_birthdays[i].update(gist_birthdays[i])
                birthdays = pk_birthdays
                day = start_day + timedelta(days=i)
                
                text = await format_birthdays_day(birthdays[i], day, self.client, header_format="")
                if text != "":
                    output += f'__{re.sub("x","",re.sub("x0","",day.strftime("%B x%d")))}__\n{text}\n'

            output = replace_user_ids_with_nicknames(self.client, output)
            await split_and_send(output, ctx.channel)

    @commands.command(aliases=["myBirthdays", "birthdayList","birthdaysList"], brief="See all of your birthdays.")
    async def listBirthdays(self, ctx):
        async with ctx.channel.typing():
            birthdays_array = []
            system = await pk.get_system_by_discord_id(ctx.author.id)

            output = "**My Birthdays:**\n"
            birthdays = await get_pk_birthdays_by_system(system.hid)
            try:
                birthdays.update(await get_gist_birthdays_by_user(ctx.author.id))
            except:
                pass

            for id, members in birthdays.items():
                birthdays_array += members
            birthdays_dict = {system.hid: birthdays_array}

            output += await format_birthdays_year(birthdays_dict)
            await split_and_send(output, ctx.channel)

    '''@commands.command(brief="See all birthdays, from all users.")
    @checks.is_vriska()
    async def listAllBirthdays(self, ctx):
        async with ctx.channel.typing():
            output = "**All Birthdays:**\n"
            birthdays = await get_pk_birthdays()
            birthdays.update(await get_gist_birthdays_by_user(ctx.author.id))

            output += await format_birthdays_year(birthdays)
            await split_and_send(output, ctx.channel)'''

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
            birthdays = await get_gist_birthdays_by_user(ctx.author.id)

        output += await format_birthdays_year(birthdays)
        await split_and_send(output, ctx.channel)

    ''' ------------------------------
             MANUAL BIRTHDAYS
        ------------------------------'''

    @commands.command(brief="Add a manual birthday.")
    async def addBirthday(self, ctx, name="", *,birthday_raw=""):
        new_birthday = Birthday(name.capitalize(), birthday_raw, ctx.author.id, True)
        
        async with ctx.channel.typing():
            birthday_conflict = None
            try:
                birthday_conflict = await get_gist_birthday_by_user_and_name(name.capitalize(), ctx.author.id)
            except checks.OtherError:
                pass
            except:
                raise
            
            if birthday_conflict != None:
                await ctx.send(f'You already have a birthday named {new_birthday.name}!')
                await ctx.invoke(self.client.get_command('updateBirthday'), name=name, birthday_raw=birthday_raw)
                return
            
            await add_gist_birthday(new_birthday)
        
        await ctx.send(f'Birthday {new_birthday.short_birthday()} set for {new_birthday.name}.')

    @commands.command(brief="Update a manual birthday.")
    async def updateBirthday(self, ctx, name="", *,birthday_raw=""):
        new_birthday = Birthday(name.capitalize(), birthday_raw, ctx.author.id, True)
        
        birthday_conflict = await get_gist_birthday_by_user_and_name(name.capitalize(), ctx.author.id)
        if birthday_conflict != None:
            menu_text = f' Would you like to replace the birthday for {name.capitalize()} on {birthday_conflict.short_birthday()} with {new_birthday.short_birthday()}?'
            result = await confirmationMenu(self.client, ctx, menu_text)
            if result == 1:
                await remove_gist_birthday(new_birthday.name, ctx.author.id)
                await add_gist_birthday(new_birthday)
                await ctx.send(f'Birthday for {new_birthday.name} updated to {new_birthday.short_birthday()}.')
                return 
            elif result == 0:
                await ctx.send("Operation cancelled.")
                return
            else:
                raise checks.FuckyError("Something be fucky here. Idk what happened. Maybe try again?")

        await add_gist_birthday(new_birthday)
        await ctx.send(f'Birthday {new_birthday.short_birthday()} set for {new_birthday.name}.')

    @commands.command(aliases=["deleteBirthday","delBirthday"],brief="Remove a manual birthday.")
    async def removeBirthday(self, ctx, name=""):
        async with ctx.channel.typing():
            await remove_gist_birthday(name, ctx.author.id)
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
            conn, cursor = database_connect()
            
            cursor.execute("SELECT * FROM pkinfo")
            data = cursor.fetchall()

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
            cursor.execute(sql_insert_query, record_to_insert)

        await ctx.send("PluralKit Birthdays successfully connected!")   
        database_disconnect(conn,cursor)

    @commands.command(brief="Disconnect your PluralKit account.")
    async def deleteSystemBirthdays(self, ctx):
        async with ctx.channel.typing():
            sql_delete_query = """DELETE FROM pkinfo WHERE id = %s"""
            system = await pk.get_system_by_discord_id(ctx.author.id)

            conn, cursor = database_connect()
            
            cursor.execute("SELECT * FROM pkinfo")
            data = cursor.fetchall()

            currently_connected = False
            
            if len(data) > 0:
                for i in data:
                    if i[0] == str(system.hid):
                        currently_connected = True
                        
            if currently_connected:
                record = (str(system.hid),)
                try:
                    cursor.execute(sql_delete_query, record)
                    await ctx.send("PluralKit account disconnected.")    
                except (Exception, psycopg2.DatabaseError) as error:
                    print(error)

            else:
                raise checks.OtherError("Your PluralKit account is already unconnected.")

        database_disconnect(conn,cursor)

    @commands.command(aliases=["addtoken","pktoken"],brief="Add a token to your PluralKit connection.")
    async def addPKToken(self, ctx):
        async with ctx.channel.typing():
            sql_update_query = "UPDATE pkinfo SET token = %s WHERE id = %s"
            system = await pk.get_system_by_discord_id(ctx.author.id)
            conn, cursor = database_connect()
            
            token = await pk.prompt_for_pk_token(self.client, ctx)

            record_to_insert = (token, str(system.hid))
            cursor.execute(sql_update_query, record_to_insert)

        await ctx.send("PluralKit Token successfully added!")
        database_disconnect(conn,cursor)

    @commands.command(brief="Set your system birthdays to show ages based on birth year.")
    async def showAge(self, ctx):
        async with ctx.channel.typing():
            sql_update_query = "UPDATE pkinfo SET show_age = True WHERE id = %s"
            system = await pk.get_system_by_discord_id(ctx.author.id)
            conn, cursor = database_connect()
            
            record_to_insert = (str(system.hid),)
            cursor.execute(sql_update_query, record_to_insert)

        await ctx.send("Your PluralKit birthdays will now show age based on birth year.")
        database_disconnect(conn,cursor)

    @commands.command(brief="Set your system birthdays to hide ages based on birth year.")
    async def hideAge(self, ctx):
        async with ctx.channel.typing():
            sql_update_query = "UPDATE pkinfo SET show_age = False WHERE id = %s"
            system = await pk.get_system_by_discord_id(ctx.author.id)
            conn, cursor = database_connect()
            
            record_to_insert = (str(system.hid),)
            cursor.execute(sql_update_query, record_to_insert)

        await ctx.send("Your PluralKit birthdays will no longer show age based on birth year.")
        database_disconnect(conn,cursor)
    
def setup(client):
    client.add_cog(Birthdays(client))
