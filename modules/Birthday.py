import datetime

from dateutil import parser
import re

import sys

class Birthday:
    name: str
    birthday: datetime.date
    year: int
    id: int

    def __init__(self, name="", birthday=None, id=None, raw=True, year=None):
        if raw:
            self.birthday = parser.parse(birthday)
            if str(self.birthday.year) not in birthday:
                self.year = -1
        else:
            self.birthday = birthday
        self.year = birthday.year if birthday.year != 4 else -1
        self.year = year if year is not None else self.year
        self.name = name
        self.id = id

    '''def __init__(self, birthday_string=""):
        groups = re.search("(.*)(.{3} \d{2} \d{4}) (\d{18})",birthday_string)
        self.name = groups.group(1)
        self.birthday = parser.parse(groups.group(2))
        self.year = self.birthday.year if self.birthday.year != 4 else -1
        self.id = int(groups.group(3))
    '''

    @classmethod
    def from_string(cls, birthday_string) -> 'Birthday':
        groups = re.search("(.*)(.{3} \d{2} (?:-1|\d{4})) (\d{18})",birthday_string)
        name = groups.group(1)
        birthday = parser.parse(groups.group(2))
        if "-1" in groups.group(2):
            year = -1
        else:
            year = None
        id = int(groups.group(3))
        return cls(name, birthday, id, False, year=year)

    def __str__(self):
        return f'{self.name} {self.birthday.strftime("%b %d")} {self.year}'

    def short_birthday(self):
        return (self.birthday.strftime("%b %d ") + str(self.year)).rstrip(" -1")
