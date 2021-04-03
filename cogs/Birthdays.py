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

from modules.functions import splitLongMsg, confirmationMenu
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
        
        #await self.client.get_channel(754527915290525807).send(str(today.date())+str(last_birthday))

        if today.date() != last_birthday:
            cursor.execute("UPDATE vars set value = %s WHERE name = 'last_birthday'", (today.date(),))
            birthdays = self.get_todays_birthdays(today.date())

            '''if len(birthdays) > 0:
                for birthday in birthdays:
                    member = self.client.get_guild(SKYS_SERVER_ID).get_member(birthday.id)
                    name = f'{member.nick} | str(member)' if member.nick is not None else str(member)
                    sys.stdout.write(str(birthday))
                    year_text = f': {today.date().year - birthday.year} years old' if birthday.year != -1 else ""
                    output += birthday.name + "(" + name + ")" + year_text + "\n"'''
            
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
                        if birthday.day == today.day and birthday.month == today.month:
                            if member.name_privacy == "private":
                                name = member.display_name
                            else:
                                name = member.name

                            year_text = ""
                            if birthday.year != 1 and birthday.year != 4:
                                if today.year - birthday.year > 0:
                                    year_text = f': {today.year - birthday.year} years old'

                            output += f'{name} {system.tag} {year_text}'

            if len(output) > 0:
                output = f'**{re.sub("x","",re.sub("x0","",today.strftime("%B x%d")))} - Today\'s Birthdays:**\n' + output
                await self.client.get_channel(754527915290525807).send(output)

        conn.commit()
        cursor.close()
        conn.close()

    @commands.command(pass_context=True)
    async def todaysBirthdays(self, ctx):
        async with ctx.channel.typing():
            output = ""
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()

            today_utc = datetime.now(tz=pytz.utc)
            today = today_utc.astimezone(timezone('US/Pacific'))
            
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
                        if birthday.day == today.day and birthday.month == today.month:
                            if member.name_privacy == "private":
                                name = member.display_name
                            else:
                                name = member.name

                            year_text = ""
                            if birthday.year != 1 and birthday.year != 4:
                                if today.year - birthday.year > 0:
                                    year_text = f': {today.year - birthday.year} years old'

                            output += f'{name} {system.tag} {year_text}\n'

            if len(output) > 0:
                output = f'**{re.sub("x","",re.sub("x0","",today.strftime("%B x%d")))} - Today\'s Birthdays:**\n' + output
                output = splitLongMsg(output)

                for o in output:
                    await self.client.get_channel(754527915290525807).send(o)

            conn.commit()
            cursor.close()
            conn.close()
        
            
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

    async def add_birthday(self, birthday: Birthday):
        async with gistSem:
            new_content = f'{gist.files["birthdays.txt"].content}{birthday.gist_string}'
            gist.edit(files={"birthdays.txt": github.InputFileContent(content=new_content)})
        
    @commands.command(pass_context=True)
    @commands.is_owner()
    async def addBirthday(self, ctx, name="", *,birthday_raw=""):
        birthday = Birthday(name, birthday_raw, ctx.author.id, True, pkid="     ")
        
        await self.add_birthday(birthday)
        
        await ctx.send(f'Birthday {birthday.short_birthday()} set for {birthday.name.capitalize()}.')

    @commands.command(pass_context=True, aliases=["deleteBirthday","delBirthday"])
    @commands.is_owner()
    async def removeBirthday(self, ctx, name=""):
        birthdays = re.split("\n",gist.files["birthdays.txt"].content)
        new_content = '\n'.join([x for x in birthdays if (str(ctx.author.id) not in x and name not in x)])
        gist.edit(files={"birthdays.txt": github.InputFileContent(content=new_content)})
            
        await ctx.send(f'Birthday removed.')

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


    @commands.command(pass_context=True, aliases=["myBirthdays", "birthdayList","birthdaysList"])
    async def listBirthdays(self, ctx):
        async with ctx.channel.typing():
            output = ""
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()
            today_utc = datetime.now(tz=pytz.utc)
            today = today_utc.astimezone(timezone('US/Pacific'))

            birthdays = []
            
            system = await pk.get_system_by_discord_id(ctx.author.id)
            
            cursor.execute("SELECT * FROM pkinfo")
            data = cursor.fetchall()

            
            for i in data:
                if system.hid == i[0]:
                    try:
                        async with aiohttp.ClientSession() as session:
                            system = await pluralKit.System.get_by_hid(session,i[0],i[1])
                            members = await system.members(session)
                    except:
                        raise checks.OtherError("I don't have access to your member list! Either set your member list to public, or run `hbs;deleteSystemBirthdays` and run `hbs;addSystemBirthdays` to share your access token.")
                    
                    for member in members:
                        if member.birthday != None and member.visibility != "private" and member.birthday_privacy != "private":
                            birthdays.append(member)
                            
                    if len(birthdays) > 0:
                        birthdays.sort(key = lambda d: (parser.parse(d.birthday).month, parser.parse(d.birthday).day, (d.display_name if d.name_privacy == "private" else d.name)))
                        for i in range(1,13):
                            new_birthdays = [b for b in birthdays if parser.parse(b.birthday).month == i]
                            if len(new_birthdays) > 0:
                                month = date(1900, i, 1).strftime('%B')
                                output += f'__{month}__\n'
                                for j in range(1,32):
                                    new_new_birthdays = [b for b in new_birthdays if parser.parse(b.birthday).day == j]
                                    if len(new_new_birthdays) > 0:
                                        day = date(1900, 1, j).strftime('%d').lstrip('0')
                                        output += f'{day}: '
                                        
                                        for member in new_new_birthdays:
                                            birthday = parser.parse(member.birthday)

                                            year_text = ""
                                            if birthday.year != 1 and birthday.year != 4:
                                                year_text = f' ({birthday.strftime("%Y")})'
                                        
                                            if (member.name_privacy == "private"):
                                                name = member.display_name
                                            else:
                                                name = member.name
                                                
                                            output += (f'{name}{year_text}, ')
                                            
                                        output = output.rstrip(", ")
                                        output += "\n"
                            
            if len(output) > 0:
                output = f'**Your Birthdays:**\n' + output
                output = splitLongMsg(output)

                for o in output:
                    await ctx.send(o)
                #await ctx.send(output)
        
    '''@commands.command(pass_context=True)
    async def listBirthdays(self, ctx):
        output = "Your Birthdays: \n"
        raw_birthdays = gist.files["birthdays.txt"].content
        raw_birthdays = re.split("\n",raw_birthdays)
        birthday_list = [Birthday.from_string(birthday) for birthday in raw_birthdays if birthday != ""]
        birthday_list = [b for b in birthday_list if b.id == ctx.author.id]
        for birthday in birthday_list:
            output += str(birthday) + "\n"
        await ctx.send(output)'''

    @commands.command(pass_context=True)
    @checks.is_vriska()
    async def listAllBirthdays(self, ctx):
        async with ctx.channel.typing():
            '''output = "Birthdays: \n"
            raw_birthdays = gist.files["birthdays.txt"].content
            raw_birthdays = re.split("\n",raw_birthdays)
            birthday_list = [Birthday.from_string(birthday) for birthday in raw_birthdays if birthday != ""]
            for birthday in birthday_list:
                output += str(birthday) + "\n"
            await ctx.send(output)'''

            output = ""
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cursor = conn.cursor()
            today_utc = datetime.now(tz=pytz.utc)
            today = today_utc.astimezone(timezone('US/Pacific'))

            birthdays = []
            
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
                        birthdays.append(member)
                        
            if len(birthdays) > 0:
                birthdays.sort(key = lambda d: (parser.parse(d.birthday).month, parser.parse(d.birthday).day, (d.display_name if d.name_privacy == "private" else d.name)))
                for i in range(1,13):
                    new_birthdays = [b for b in birthdays if parser.isoparse(b.birthday).month == i]
                    if len(new_birthdays) > 0:
                        month = date(1900, i, 1).strftime('%B')
                        output += f'__{month}__\n'
                        for j in range(1,32):
                            new_new_birthdays = [b for b in new_birthdays if parser.parse(b.birthday).day == j]
                            if len(new_new_birthdays) > 0:
                                day = date(1900, 1, j).strftime('%d').lstrip('0')
                                output += f'{day}: '
                                
                                for member in new_new_birthdays:
                                    birthday = parser.parse(member.birthday)

                                    year_text = ""
                                    if birthday.year != 1 and birthday.year != 4:
                                        year_text = f' ({birthday.strftime("%Y")})'
                                
                                    if (member.name_privacy == "private"):
                                        name = member.display_name
                                    else:
                                        name = member.name
                                        
                                    output += (f'{name}{year_text}, ')
                                    
                                output = output.rstrip(", ")
                                output += "\n"
                            
            if len(output) > 0:
                output = f'**Birthdays:**\n' + output
                output = splitLongMsg(output)

                for o in output:
                    await ctx.send(o)
                       
def setup(client):
    client.add_cog(Birthdays(client))
