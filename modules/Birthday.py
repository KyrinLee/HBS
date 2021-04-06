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
        self.year = -1
        if raw:
            self.birthday = parser.parse(birthday)
            if str(self.birthday.year) in birthday:
                self.year = self.birthday.year
        else:
            self.birthday = birthday
            
        if year is not None:
            self.year = year
        
        self.name = name.rstrip()
        self.id = id

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
        return (re.sub(" -1$", " ", self.birthday.strftime("%b %d ") + str(self.year)))

    def gist_birthday(self):
        txt = (f'{self.name} {self.birthday.strftime("%b %d")} {self.year} {self.id}\n')
        return txt
