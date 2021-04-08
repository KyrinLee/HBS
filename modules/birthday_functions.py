from itertools import groupby
import aiohttp
import asyncio

import re

from datetime import datetime, date
import github
from github import Github

from pytz import timezone
import pytz

from modules.functions import *
from modules import checks, pk, pluralKit
from modules.Birthday import Birthday
from resources.constants import *

gistSem = asyncio.Semaphore(1)

g = Github(os.environ['GIST_TOKEN'])
gist = g.get_gist(os.environ['BIRTHDAYS_GIST_ID'])

NO_PK_BIRTHDAYS_SET = "You have no birthdays set in PluralKit!"
NO_GIST_BIRTHDAYS_SET = "You have no manual birthdays set! Use `hbs;addBirthday` to add a manual birthday!"
NO_ACCESS = "I don't have access to your member list!"

def replace_user_ids_with_nicknames(client, txt):
    pat = re.compile("<([0-9]{18})>")

    def repl(id):
        user = client.get_user(int(id.group(1)))
        return f'({user})'
    
    return pat.sub(repl, txt)

async def format_birthdays_year(birthday_dict):
    if birthday_dict == None:
        return ""
    output = ""
    for id, members in birthday_dict.items():
        if len(members) > 0:
            members.sort(key = lambda d: (d.birthday.month, d.birthday.day, d.name))
            for month_key, month_group in groupby(members, lambda x: x.birthday.month):
                month = date(1900, month_key, 1).strftime('%B')
                output += f'__{month}__\n'
                for day_key, day_group in groupby(month_group, lambda x: x.birthday.day):
                    output += str(day_key) + ": "
                    for member in day_group:
                        birthday = member.birthday
                        year_text = ''
                        if member.year not in [-1,1,4]:
                            year_text = f' ({birthday.strftime("%Y")})'
                    
                        output += (f'{member.name}{year_text}, ')
                    output = output.rstrip(", ")
                    output += "\n"
    return output

async def format_birthdays_day(birthday_dict, day, client, header_format=None):
    if birthday_dict == None:
        return ""

    output = ""
    final_birthdays = []
    today = get_today()
    
    if header_format == None:
        if (day.year == today.year and day.month == today.month and day.day == today.day):
            output += f'**{re.sub("x","",re.sub("x0","",day.strftime("%B x%d, %Y")))} - Today\'s Birthdays'
        else:
            output += f'**{re.sub("x","",re.sub("x0","",day.strftime("%B x%d, %Y")))}\'s Birthdays'
    else:
        output += header_format

    for id, members in birthday_dict.items():
        tag = await pk.get_system_tag_by_pk_id(id) if (len(str(id)) == 5) else f'<{str(id)}>'
        if not isinstance(members, str):
            for member in members:
                age_text = ""
                birthday = member.birthday
                if member.year not in [-1,1,4]:
                    if calculate_age(birthday, day) > 0:
                        age_text = f': {calculate_age(birthday, day)} years old'
                final_birthdays.append(f'{member.name} {tag}{age_text}')

    final_birthdays = sorted(final_birthdays, key=str.lower)
    output += escapeCharacters("\n".join(final_birthdays))

    return output
    
def calculate_age(born, on_date=None):
    if on_date == None:
        on_date = get_today()
    return on_date.year - born.year - ((on_date.month, on_date.day) < (born.month, born.day))


#PLURALKIT BIRTHDAY FUNCTIONS

async def get_pk_birthdays():
    birthday_dict = {}
    conn, cursor = database_connect()

    cursor.execute("SELECT * FROM pkinfo")
    data = cursor.fetchall()

    for i in data:
        system_birthdays = []
        try:
            async with aiohttp.ClientSession() as session:
                system = await pluralKit.System.get_by_hid(session,i[0],i[1])
                members = await system.members(session)

            if len(members) == 0:
                system_birthdays = NO_PK_BIRTHDAYS_SET
                
            else:
                for member in members:
                    if member.birthday != None and member.visibility != "private" and member.birthday_privacy != "private":
                        name = member.display_name if member.name_privacy == "private" else member.name
                        system_birthdays.append(Birthday(name=name, birthday=member.birthday, raw=True))
                
        except:
            system_birthdays = NO_ACCESS + "\nEither set your member list to public, or run `hbs;addPKToken` to share your access token."

        birthday_dict[i[0]] = system_birthdays

    database_disconnect(conn, cursor)

    return birthday_dict

async def get_pk_birthdays_by_system(system_id):
    birthday_dict = await get_pk_birthdays()
    birthdays = birthday_dict[system_id]
    
    if birthdays == NO_PK_BIRTHDAYS_SET:
        raise checks.OtherError(NO_PK_BIRTHDAYS_SET)
    elif birthdays == NO_ACCESS:
        raise checks.OtherError(NO_ACCESS)
    
    return {system_id: birthdays}

async def get_pk_birthdays_by_day(search_day):
    birthday_dict = {}
    all_birthdays = await get_pk_birthdays()

    for system_id, members in all_birthdays.items():
        if not isinstance(members, str):
            birthday_dict[system_id] = [member for member in members if (member.birthday.day == search_day.day and member.birthday.month == search_day.month)]
           
    return birthday_dict

async def get_pk_birthdays_by_date_range(start_day, end_day):
    day_array = []
    all_birthdays = await get_pk_birthdays()      
    
    day = start_day
    while day <= end_day:
        birthday_dict = {}
        for system_id, members in all_birthdays.items():
            if not isinstance(members, str):
                birthday_dict[system_id] = [m for m in members if (m.birthday.month == day.month and m.birthday.day == day.day)]
        day_array.append(birthday_dict)
        day += timedelta(days=1)
            
    return day_array

#MANUAL BIRTHDAY FUNCTIONS

async def get_gist_birthdays():
    birthday_dict = {}
    async with gistSem:
        raw_birthdays = gist.files["birthdays.txt"].content
        raw_birthdays = re.split("\n",raw_birthdays)
        birthday_list = [Birthday.from_string(birthday) for birthday in raw_birthdays if birthday != ""]
    for user_id, members in groupby(birthday_list, lambda x: x.id):
        if user_id != 0:
            members = list(members)
            members.sort(key = lambda d: (d.birthday.month, d.birthday.day, d.name))
            if len(members) == 0:
                members = NO_GIST_BIRTHDAYS_SET
            birthday_dict[user_id] = members
            
    return birthday_dict

async def get_gist_birthdays_by_day(search_day):
    birthday_dict = {}
    all_birthdays = await get_gist_birthdays()
            
    for user_id, birthdays in all_birthdays.items():
        birthday_dict[user_id] = [b for b in birthdays if (b.birthday.month == search_day.month and b.birthday.day == search_day.day)]

    return birthday_dict

async def get_gist_birthdays_by_date_range(start_day, end_day):
    day_array = []
    all_birthdays = await get_gist_birthdays()
    
    day = start_day
    while day <= end_day:
        birthday_dict = {}
        for user_id, birthdays in all_birthdays.items():
            birthday_dict[user_id] = [b for b in birthdays if (b.birthday.month == day.month and b.birthday.day == day.day)]
        day_array.append(birthday_dict)
        day += timedelta(days=1)
    return day_array

async def get_gist_birthdays_by_user(user_id):
    birthday_dict = await get_gist_birthdays()
    try:
        birthdays = birthday_dict[user_id]
    except:
        raise checks.OtherError(NO_GIST_BIRTHDAYS_SET)
    
    return {user_id: birthdays}

async def get_gist_birthday_by_user_and_name(name, user_id):
    birthdays_dict = await get_gist_birthdays_by_user(user_id)
    birthdays = [b for b in birthdays_dict[user_id] if b.name == name]
    if len(birthdays) > 0:
        return birthdays[0]
    else:
        return None

async def add_gist_birthday(birthday):
    new_content = f'{gist.files["birthdays.txt"].content}{birthday.gist_birthday()}'
    gist.edit(files={"birthdays.txt": github.InputFileContent(content=new_content)})

async def remove_gist_birthday(name, id):
    deleting_birthday = await get_gist_birthday_by_user_and_name(name, id)
    if deleting_birthday != None:
        new_content = re.sub(deleting_birthday.gist_birthday(), "", gist.files["birthdays.txt"].content)
        gist.edit(files={"birthdays.txt": github.InputFileContent(content=new_content)})
