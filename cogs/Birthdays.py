import discord
from discord.ext import tasks, commands
import sys

import os

import github
from github import Github
from dateutil import parser
import re

from modules import checks, pk, pluralKit
from modules.Birthday import Birthday
from modules import pluralKit

from modules.functions import splitLongMsg, confirmationMenu, escapeCharacters
from resources.constants import *

import psycopg2

from datetime import datetime, date

import aiohttp
import asyncio

from pytz import timezone
import pytz

# or using an access token
g = Github(os.environ['GIST_TOKEN'])

# Then play with your Github objects:
gist = g.get_gist(os.environ['BIRTHDAYS_GIST_ID'])

gistSem = asyncio.Semaphore(1)

def format_birthdays_year(birthdays):
    output = ""
    if len(birthdays) > 0:
        birthdays.sort(key = lambda d: (d.birthday.month, d.birthday.day, d.name))
        for i in range(1,13):
            new_birthdays = [b for b in birthdays if b.birthday.month == i]
            if len(new_birthdays) > 0:
                month = date(1900, i, 1).strftime('%B')
                output += f'__{month}__\n'
                for j in range(1,32):
                    new_new_birthdays = [b for b in new_birthdays if b.birthday.day == j]
                    if len(new_new_birthdays) > 0:
                        day = date(1900, 1, j).strftime('%d').lstrip('0')
                        output += f'{day}: '
                        
                        for member in new_new_birthdays:
                            birthday = member.birthday

                            year_text = ""
                            if birthday.year != 1 and birthday.year != 4:
                                year_text = f' ({birthday.strftime("%Y")})'
                        
                            output += (f'{member.name}{year_text}, ')
                            
                        output = output.rstrip(", ")
                        output += "\n"
    return output

def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

class DuplicateBirthday(Exception):
    def __init__(self, *args, **kwargs):
        self.conflictBirthday = kwargs.pop("conflict",None)
        self.newBirthday = kwargs.pop("birthday",None)
        super().__init__(*args, **kwargs)
        self.__dict__.update(kwargs)
    pass

class Birthdays(commands.Cog):
    def __init__(self, client):
        self.client = client

    @tasks.loop(seconds=30.0)
    async def time_check(self):
        output = ""
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()

        today_utc = datetime.now(tz=pytz.utc)
        today = today_utc.astimezone(timezone('US/Pacific'))
        
        cursor.execute("SELECT * FROM vars WHERE name = 'last_birthday'")
        data = cursor.fetchall()
        if len(data[0]) == 0:
            last_birthday_string = "0000-00-00"
        else:
            last_birthday_string = data[0][1]

        last_birthday = parser.parse(last_birthday_string).date()

        if today.date() != last_birthday:
            channel = self.client.get_channel(754527915290525807)
            cursor.execute("UPDATE vars set value = %s WHERE name = 'last_birthday'", (today.date(),))
            birthdays = self.get_todays_birthdays(today.date())

            output = get_days_birthdays(channel)
            for o in output:
                await channel.send(o)
            
        conn.commit()
        cursor.close()
        conn.close()

    ''' ------------------------------
            GETTING BIRTHDAYS
        ------------------------------'''
        
    @commands.command(pass_context=True)
    async def todaysBirthdays(self, ctx):
        today = datetime.now(tz=pytz.utc).astimezone(timezone('US/Pacific'))
        
        output = f'**{re.sub("x","",re.sub("x0","",today.strftime("%B x%d, %Y")))} - Today\'s Birthdays:**\n'
        output += await self.get_days_birthdays(ctx.channel, search_day=today)
        output = splitLongMsg(output)
        for o in output:
            await ctx.send(o)

    @commands.command(pass_context=True)
    async def birthdays(self, ctx, *, day=None):
        if day == "today":
            day = datetime.now(tz=pytz.utc).astimezone(timezone('US/Pacific')) 
        else:
            day = parser.parse(day)
            
        output = f'**{re.sub("x","",re.sub("x0","",day.strftime("%B x%d, %Y")))} - Birthdays:**\n'
        output += await self.get_days_birthdays(ctx.channel, search_day=day)
        output = splitLongMsg(output)
        for o in output:
            await ctx.send(o)

    async def get_days_birthdays(self, channel, search_day=None):
        if search_day == None:
            today_utc = datetime.now(tz=pytz.utc)
            search_day = today_utc.astimezone(timezone('US/Pacific'))
            
        async with channel.typing():
            output = ""
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM pkinfo")
            data = cursor.fetchall()

            for i in data:
                try:
                    async with aiohttp.ClientSession() as session:
                        system = await pluralKit.System.get_by_hid(session,i[0],i[1])
                        members = await system.members(session)
                except:
                    pass
                for member in members:
                    if member.birthday != None and member.visibility != "private" and member.birthday_privacy != "private":
                        birthday = parser.isoparse(member.birthday)
                        if birthday.day == search_day.day and birthday.month == search_day.month:
                            if member.name_privacy == "private":
                                name = member.display_name
                            else:
                                name = member.name

                            year_text = ""
                            if birthday.year != 1 and birthday.year != 4:
                                if search_day.year - birthday.year > 0:
                                    year_text = f': {search_day.year - birthday.year} years old'

                            output += f'{name} {system.tag} {year_text}\n'

            conn.commit()
            cursor.close()
            conn.close()

            output = escapeCharacters(output)
            return output


    ''' ------------------------------
             MANUAL BIRTHDAYS
        ------------------------------'''

    async def add_birthday(self, birthday: Birthday):
        async with gistSem:
            new_content = f'{gist.files["birthdays.txt"].content}{birthday.gist_birthday()}'
            gist.edit(files={"birthdays.txt": github.InputFileContent(content=new_content)})
        
    @commands.command(pass_context=True)
    @commands.is_owner()
    async def addBirthday(self, ctx, name="", *,birthday_raw=""):
        birthday = Birthday(name.capitalize(), birthday_raw, ctx.author.id, True)
        
        await self.add_birthday(birthday)
        
        await ctx.send(f'Birthday {birthday.short_birthday()} set for {birthday.name}.')

    @commands.command(pass_context=True, aliases=["deleteBirthday","delBirthday"])
    @commands.is_owner()
    async def removeBirthday(self, ctx, name=""):
        birthdays = re.split("\n",gist.files["birthdays.txt"].content)
        new_content = '\n'.join([x for x in birthdays if (str(ctx.author.id) not in x and name not in x)])
        gist.edit(files={"birthdays.txt": github.InputFileContent(content=new_content)})
            
        await ctx.send(f'Birthday removed.')

    def get_todays_birthdays(self, day):
        birthday_list = []
        todays_birthdays = []
        
        raw_birthdays = gist.files["birthdays.txt"].content
        raw_birthdays = re.split("\n",raw_birthdays)
        #for birthday in raw_birthdays:
        #sys.stdout.write(str(birthday_list))
        birthday_list = [Birthday.from_string(birthday) for birthday in raw_birthdays if birthday != ""]
            
        for birthday in birthday_list:
            if birthday.birthday.date().month == day.month and birthday.birthday.date().day == day.day:
                todays_birthdays.append(birthday)

        #await ctx.send(str(birthday_list))
        return todays_birthdays

    async def get_systems_birthdays(self, system_id, auth):
        birthdays = []
        
        try:
            async with aiohttp.ClientSession() as session:
                system = await pluralKit.System.get_by_hid(session,system_id, auth)
                members = await system.members(session)
        except:
            raise checks.OtherError("I don't have access to your member list! Either set your member list to public, or run `hbs;deleteSystemBirthdays` and run `hbs;addSystemBirthdays` to share your access token.")
        
        for member in members:
            if member.birthday != None and member.visibility != "private" and member.birthday_privacy != "private":
                name = member.display_name if member.name_privacy == "private" else member.name
                birthdays.append(Birthday(name=name, birthday=member.birthday, raw=True))
                
        return birthdays

    async def get_gist_user_birthdays(self, user_id):
        birthdays = []
        raw_birthdays = gist.files["birthdays.txt"].content
        raw_birthdays = re.split("\n",raw_birthdays)
        birthday_list = [Birthday.from_string(birthday) for birthday in raw_birthdays if birthday != ""]
        birthday_list = [b for b in birthday_list if b.id == user_id]

        for birthday in birthday_list:
            birthdays.append(birthday)

        return birthdays
    
    ''' ------------------------------
            SYSTEM BIRTHDAYS
        ------------------------------'''

    @commands.command(pass_context=True)
    async def addSystemBirthdays(self, ctx):
        sql_insert_query = """ INSERT INTO pkinfo (id, token) VALUES (%s,%s)"""
        token = ""
        
        system = await pk.get_system_by_discord_id(ctx.author.id)

        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
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
            await ctx.send("Your member list is currently private. Check your DMs for information about an authorization token to enable linking your PK account.")
            token = await pk.prompt_for_pk_token(self.client, ctx)
            

        record_to_insert = (str(system.hid), token)
        cursor.execute(sql_insert_query, record_to_insert)
        await ctx.send("PluralKit Birthdays successfully connected!")
            
        conn.commit()
        cursor.close()
        conn.close()

    @commands.command(pass_context=True)
    async def deleteSystemBirthdays(self, ctx):
        sql_delete_query = """DELETE FROM pkinfo WHERE id = %s"""
        system = await pk.get_system_by_discord_id(ctx.author.id)

        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = conn.cursor()
        
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

        conn.commit()
        cursor.close()
        conn.close()

    '''---------------------------
            LIST BIRTHDAYS
    ------------------------------'''

    async def list_birthdays(self, ctx, include_system, include_gist, include_all):
        async with ctx.channel.typing():
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()
            
            today = datetime.now(tz=pytz.utc).astimezone(timezone('US/Pacific'))
            output = f'**Your Birthdays:**\n'
            birthdays = []
            
            system = await pk.get_system_by_discord_id(ctx.author.id)
            
            cursor.execute("SELECT * FROM pkinfo")
            data = cursor.fetchall()
            
            if include_system:
                for i in data:
                    if include_all == True or system.hid == i[0]:
                        try:
                            birthdays += await self.get_systems_birthdays(i[0],i[1])
                        except:
                            raise

            if include_gist:
                birthdays = birthdays + await self.get_gist_user_birthdays(ctx.author.id)
                            
            output = format_birthdays_year(birthdays)
            output = splitLongMsg(escapeCharacters(output))

            return output

    @commands.command(pass_context=True, aliases=["myBirthdays", "birthdayList","birthdaysList"])
    async def listBirthdays(self, ctx):
        output = await self.list_birthdays(ctx, include_system=True, include_gist = True, include_all=False)
        for o in output:
            await ctx.send(o)

    @commands.command(pass_context=True)
    @checks.is_vriska()
    async def listAllBirthdays(self, ctx):
        output = await self.list_birthdays(ctx, include_system=True, include_gist = True, include_all=True)
        for o in output:
            await ctx.send(o)

    @commands.command(pass_context=True)
    async def listSystemBirthdays(self, ctx):
        output = await self.list_birthdays(ctx, include_system=True, include_gist = False, include_all=False)
        for o in output:
            await ctx.send(o)

    @commands.command(pass_context=True)
    async def listManualBirthdays(self, ctx):
        output = await self.list_birthdays(ctx, include_system=False, include_gist = True, include_all=False)
        for o in output:
            await ctx.send(o)

    
def setup(client):
    client.add_cog(Birthdays(client))
