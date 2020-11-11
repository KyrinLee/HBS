import discord
from discord.ext import commands
import sys

import os

import asyncio
import checks
import functions

DATABASE_URL = os.environ['DATABASE_URL']

class HelpMenu(commands.Cog):
    def __init__(self, client):
        self.client = client
