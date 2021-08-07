from itertools import groupby
import aiohttp
import asyncio

import re

from datetime import datetime, date

from pytz import timezone
import pytz
import time

from modules.functions import *
from modules import checks, pk, pluralKit
from modules.Birthday import Birthday
from resources.constants import *

sql_insert_query = """INSERT INTO birthdays (name, day, month, year, id, show_age) VALUES (%s,%s,%s,%s,%s,%s)"""
sql_delete_query = """DELETE FROM birthdays where name = %s and id = %s"""
NO_PK_BIRTHDAYS_SET = "You have no birthdays set in PluralKit!"
NO_MANUAL_BIRTHDAYS_SET = "You have no manual birthdays set! Use `hbs;addBirthday` to add a manual birthday!"
NO_ACCESS = "I don't have access to your member list!"

def sort_birthday_list(birthdays):
    birthdays.sort(key = lambda b: (b.month, b.day, b.name))
    return birthdays
    
def calculate_age(birthday, on_date):
    if birthday.year not in [-1,1,4] and birthday.show_age:
        age = on_date.year - birthday.year - ((on_date.month, on_date.day) < (birthday.month, birthday.day))
        return age
    else:
        return -1

def replace_user_ids_with_nicknames(client, txt):
    def repl(id):
        user = client.get_user(int(id.group(1)))
        return f'({user})'
    
    pat = re.compile("<([0-9]{18})>")
    return pat.sub(repl, txt)

async def format_birthdays_year(birthdays):
    output = ""
    if birthdays == []:
        return output
    
    birthdays = sort_birthday_list(birthdays)
    
    for month_key, month_group in groupby(birthdays, lambda x: x.month):
        month = date(1900, month_key, 1).strftime('%B')
        output += f'__{month}__\n'
        month_group = list(month_group)
        for day_key, day_group in groupby(month_group, lambda x: x.day):
            output += str(day_key) + ": "
            for member in day_group:
                year_text = ''
                if member.show_age and member.year not in [-1,1,4]:
                    year_text = f' ({member.year})'
            
                output += (f'{member.name}{year_text}, ')
            output = output.rstrip(", ")
            output += "\n"
    
    return output

async def format_birthdays_day(birthdays, day, client):
    output = ""
    final_birthdays = []
    today = get_today()
    
    if (day == today):
        output += f'**{re.sub("x","",re.sub("x0","",day.strftime("%B x%d, %Y")))} - Today\'s Birthdays:**\n'
    else:
        output += f'**{re.sub("x","",re.sub("x0","",day.strftime("%B x%d, %Y")))}\'s Birthdays:**\n'

    if birthdays == []:
        return output

    birthdays = sort_birthday_list(birthdays)

    for member in birthdays:
        tag = member.tag if (len(member.id) == 5) else f'<{str(member.id)}>'
        age = calculate_age(member, day)
        age_text = f': {age} years old' if age != -1 and member.show_age else ""
        final_birthdays.append(f'{member.name} {tag}{age_text}')
        
    output += escapeCharacters("\n".join(final_birthdays))
    output = replace_user_ids_with_nicknames(client, output) + "\n"
    return output

#PLURALKIT BIRTHDAY FUNCTIONS

async def get_pk_birthdays():
    final_array = []
    pk_errors = {}

    data = await run_query("SELECT * FROM pkinfo")

    async with aiohttp.ClientSession() as session:
        for i in data:
            system_birthdays = []
            try:
                system = await pluralKit.System.get_by_hid(session,i[0],i[1])
                members = await system.members(session)

                if len(members) == 0:
                    pk_errors[i[0]] = checks.OtherError(NO_PK_BIRTHDAYS_SET)
                    
                else:
                    for member in members:
                        if member.birthday != None and member.visibility != "private" and member.birthday_privacy != "private":
                            name = member.display_name if member.name_privacy == "private" else member.name
                            tag = system.tag
                            system_birthdays.append(Birthday.from_raw(name, member.birthday, i[0], bool(i[2]), tag))
                    
            except:
                pk_errors[i[0]] = checks.OtherError(NO_ACCESS + "\nEither set your member list to public, or run `hbs;addPKToken` to share your access token.")

            final_array += system_birthdays

    return final_array, pk_errors

async def get_all_pk_birthdays():
    birthdays, errors = await get_pk_birthdays()
    for e in errors:
        sys.stdout.write(e)
    return birthdays

async def get_pk_birthdays_by_system(system_id):
    birthdays, errors = await get_pk_birthdays()
    error = errors.pop(system_id, None)
    if error != None:
        raise error
    return [b for b in birthdays if b.id == system_id]
        
async def get_pk_birthdays_by_day(search_day):
    birthdays = await get_all_pk_birthdays()
    return [b for b in birthdays if b.same_day_as(search_day)]

async def get_pk_birthdays_by_date_range(start_day, end_day):
    birthdays = await get_all_pk_birthdays()
    return [b for b in birthdays if b.in_date_range(start_day, end_day)]

#MANUAL BIRTHDAY FUNCTIONS

async def get_manual_birthdays():
    birthdays = []

    data = await run_query("SELECT * FROM birthdays")
    for row in data:
        birthdays.append(Birthday.from_database_row(row))
        
    return birthdays

async def get_manual_birthdays_by_day(search_day):
    birthdays = []
    data = await run_query(f'SELECT * FROM birthdays WHERE day = %s AND month = %s',(search_day.day, search_day.month))
    for row in data:
        birthdays.append(Birthday.from_database_row(row))

    return birthdays

async def get_manual_birthdays_by_date_range(start_day, end_day):
    birthdays = []
    query = "SELECT * FROM birthdays WHERE day >= %s AND month >= %s AND day <= %s AND month <= %s"
    values = (start_day.day, start_day.month, end_day.day, end_day.month)
    data = await run_query(query, values)
    
    for row in data:
        birthdays.append(Birthday.from_database_row(row))

    return birthdays

async def get_manual_birthdays_by_user(user_id):
    birthdays = []
    data = await run_query(f'SELECT * FROM birthdays WHERE id = %s', (str(user_id),))

    for row in data:
        birthdays.append(Birthday.from_database_row(row))
        
    return birthdays

async def get_manual_birthday_by_user_and_name(name, user_id):
    birthdays = []
    birthdays = await run_query(f'SELECT * FROM birthdays WHERE name = %s and id = %s', (name, str(user_id)))
        
    result = Birthday.from_database_row(birthdays[0]) if len(birthdays) > 0 else None
    return result

async def add_manual_birthday(birthday):
    insert_values = (birthday.name, birthday.day, birthday.month, birthday.year, birthday.id, birthday.show_age)
    await run_query(sql_insert_query, insert_values)

async def update_manual_birthday(birthday):
    update_query = """UPDATE birthdays SET (day, month, year) = (%s, %s, %s) WHERE name = %s AND id = %s"""
    insert_values = (birthday.day, birthday.month, birthday.year, birthday.name, birthday.id)
    await run_query(update_query, insert_values)

async def delete_manual_birthday(name, id):
    delete_values = (name, str(id))
    await run_query(sql_delete_query, delete_values)
