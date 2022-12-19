import discord
from discord.ext import commands
import sys

import psycopg2
from psycopg2 import Error

import json
import re

import asyncio

from modules.checks import FuckyError
from modules import checks

from modules.functions import *
from resources.constants import *

class AdminCommands(commands.Cog, name="Admin Commands"):
    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        if not ctx.guild.id == SKYS_SERVER_ID:
            raise checks.WrongServer()
        return True
    
async def setup(client):
    await client.add_cog(AdminCommands(client))
        
