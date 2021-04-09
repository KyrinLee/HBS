import discord
from discord.ext import tasks, commands

import datetime
from datetime import date
from dateutil import parser
import re

import sys

from modules import checks

class Birthday:
    name: str
    day: int
    month: int
    year: int
    id: str
    show_age: bool
    tag: str

    def __init__(self, name="", day=None, month=None, year=None, id=None, show_age=False, tag=""):
        self.name = name.rstrip()
        self.day = day
        self.month = month
        self.year = year
        self.id = str(id)
        self.show_age = show_age
        self.tag = tag

    @classmethod
    def from_raw(cls, name, birthday_string, id, show_age=False, tag="") -> 'Birthday':
        try:
            birthday = parser.parse(birthday_string)
        except:
            raise

        year = -1
        if str(birthday.year) in birthday_string:
            year = birthday.year
            
        return cls(name, birthday.day, birthday.month, year, id, show_age, tag)

    @classmethod
    def from_database_row(cls, row) -> 'Birthday':
        return cls(row[0], row[1], row[2], row[3], row[4], row[5])

    def __str__(self):
        return f'{self.name} {self.birthday.strftime("%b %d")} {self.year}'

    def same_day_as(self, day):
        if self.month == day.month and self.day == day.day:
            return True
        return False

    def in_date_range(self, start_day, end_day):
        test_date = datetime.datetime(start_day.year, self.month, self.day, tzinfo=pytz.utc).astimezone(timezone('US/Pacific'))
        if test_date >= start_day and test_date <= end_day:
            return True
        return False

    def short_birthday(self):
        birthday = date(1900, self.month, self.day)
        return (re.sub(" -1$", "", birthday.strftime("%b %d ") + str(self.year)))

