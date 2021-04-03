import discord
from discord.ext import tasks, commands
import sys

import os

import github
from github import Github
from dateutil import parser
import re

from modules import checks, pk
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

class DuplicateBirthday(Exception):
    def __init__(self, *args, **kwargs):
        self.conflictBirthday = kwargs.pop("conflict",None)
        self.newBirthday = kwargs.pop("birthday",None)
        super().__init__(*args, **kwargs)
        self.__dict__.update(kwargs)
    pass

class BirthdaysOLD(commands.Cog):
    def __init__(self, client):
        self.client = client

    @tasks.loop(seconds=30.0)
    async def time_check(self):
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

            if len(birthdays) > 0:
                output = f'**{re.sub("x","",re.sub("x0","",today.strftime("%B x%d")))} - Today\'s Birthdays:**\n'
                for birthday in birthdays:
                    member = self.client.get_guild(SKYS_SERVER_ID).get_member(birthday.id)
                    name = f'{member.nick} | str(member)' if member.nick is not None else str(member)
                    #sys.stdout.write(str(birthday))
                    year_text = f': {today.date().year - birthday.year} years old' if birthday.year != -1 else ""
                    output += birthday.name + "(" + name + ")" + year_text + "\n" 
                await self.client.get_channel(754527915290525807).send(output)

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
    @commands.is_owner()
    async def addSystemBirthdays(self, ctx):

    '''@commands.command(pass_context=True)
    @commands.is_owner()
    async def addSystemBirthdays(self, ctx):
        private_birthday_members = []
        no_birthday_members = []
        system = await pk.get_system_by_discord_id(ctx.author.id)
        
        if str(system.hid) in gist.files["birthdays.txt"].content:
            result = await confirmationMenu(self.client, ctx, "Your system birthdays have already been added. Would you like to delete all saved birthdays and replace them with your current PluralKit birthdays?\nNote, this will not remove birthdays that are not connected to your PK account.")
            if result == 1:
                async with ctx.channel.typing():
                    async with gistSem:
                        birthdays = re.split("\n",gist.files["birthdays.txt"].content)
                        new_content = '\n'.join([x for x in birthdays if str(system.hid) not in x])
                        gist.edit(files={"birthdays.txt": github.InputFileContent(content=new_content)})
                        await ctx.send("PluralKit birthdays removed.")
            elif result == 0:
                await ctx.send("Operation cancelled.")
            else:
                raise checks.FuckyError("Something be fucky here. Idk what happened. Ping Vriska, she'll love it.")
                

        async with ctx.channel.typing():
            output = "**Successfully added birthdays:**\n"
            
            pk_members = await pk.get_system_members_by_discord_id(ctx.author.id)
            
            for member in pk_members:
                if member.birthday_privacy == "private":
                    private_birthday_members.append(member)
                elif member.birthday == None:
                    no_birthday_members.append(member)
                else:
                    birthday = Birthday(member.name, datetime.strptime(member.birthday,("%Y-%m-%d")), ctx.author.id, raw=False, pkid=str(system.hid))
                    await self.add_birthday(birthday)
                        
                    output += f'{birthday.name}: {birthday.short_birthday()}\n'

            '''if len(private_birthday_members) > 0:
                private_birthday_members.sort(key=lambda x: x.name)
                output += "\nBirthday addition for the following members failed, because their birthdays are set to Private: "
                for member in private_birthday_members:
                    output += f'{member.name}, '
                output = output.rstrip(', ')

            if len(no_birthday_members) > 0:
                no_birthday_members.sort(key=lambda x: x.name)
                output += "\nBirthday addition for the following members failed, because they do not have set birthdays: "
                for member in no_birthday_members:
                    output += f'{member.name}, '
                output = output.rstrip(', ')'''

            output += "\nIf you have hidden members or members with private birthdays, their birthdays have not been added."

            output_array = splitLongMsg(output)
            for o in output_array:
                await ctx.send(o)

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def deleteSystemBirthdays(self, ctx):
        system = await pk.get_system_by_discord_id(ctx.author.id)
        
        if str(system.hid) in gist.files["birthdays.txt"].content:
            result = await confirmationMenu(self.client, ctx, "Are you sure you would like to remove all birthdays connected to your PluralKit account?")
            if result == 1:
                async with ctx.channel.typing():
                    async with gistSem:
                        birthdays = re.split("\n",gist.files["birthdays.txt"].content)
                        new_content = '\n'.join([x for x in birthdays if str(system.hid) in x])
                        gist.edit(files={"birthdays.txt": github.InputFileContent(content=new_content)})
                        await ctx.send("PluralKit birthdays removed.")
            elif result == 0:
                await ctx.send("Operation cancelled.")
            else:
                raise checks.FuckyError("Something be fucky here. Idk what happened. Ping Vriska, she'll love it.")
        else:
            await ctx.send("You do not have any birthdays logged attached to your PluralKit account.")'''

    @commands.command(pass_context=True)
    async def listBirthdays(self, ctx):
        output = "Your Birthdays: \n"
        raw_birthdays = gist.files["birthdays.txt"].content
        raw_birthdays = re.split("\n",raw_birthdays)
        birthday_list = [Birthday.from_string(birthday) for birthday in raw_birthdays if birthday != ""]
        birthday_list = [b for b in birthday_list if b.id == ctx.author.id]
        for birthday in birthday_list:
            output += str(birthday) + "\n"
        await ctx.send(output)

    @commands.command(pass_context=True)
    @commands.is_owner()
    async def listAllBirthdays(self, ctx):
        output = "Birthdays: \n"
        raw_birthdays = gist.files["birthdays.txt"].content
        raw_birthdays = re.split("\n",raw_birthdays)
        birthday_list = [Birthday.from_string(birthday) for birthday in raw_birthdays if birthday != ""]
        for birthday in birthday_list:
            output += str(birthday) + "\n"
        await ctx.send(output)

        
                       
def setup(client):
    client.add_cog(Birthdays(client))
