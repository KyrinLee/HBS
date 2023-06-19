from modules.functions import *
from modules import checks, pk, pluralKit
from resources.constants import *
import random, string

async def generate_reminder_id():
    keys = await run_query("SELECT reminder_id FROM reminders")
    keys.append('')

    key = ''
    while key in(keys):
        key = ''.join(random.choices(string.ascii_lowercase, k=5))

    return key
    
async def get_timezone(user_id):
    timezones = await run_query("SELECT * FROM timezones WHERE user_id = %s", (str(user_id),))
    if len(timezones) == 0:
        return None
    else:
        return pytz.timezone(timezones[0][1])
    
async def add_reminder(user_id, name, next_timestamp, repeat_type=False, repeat_info="", repeat_until=None):
    reminder_id = await generate_reminder_id()
    sql_insert_query = "INSERT INTO reminders VALUES (%s,%s,%s,%s,%s,%s,%s)"

    data = await run_query(sql_insert_query, (reminder_id, user_id, name, next_timestamp, repeat_type, repeat_info, repeat_until))

async def delete_reminder(reminder_id):
    sql_delete_query = "DELETE FROM reminders WHERE reminder_id = %s"
    data = await run_query(sql_delete_query, (reminder_id,))