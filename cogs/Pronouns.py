import discord
from discord.ext import commands
import sys

class Pronouns(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(pass_context=True,aliases=['pronouns add', 'p a', 'p add'],brief="Change game in bot's status.")
    @commands.is_owner()
    async def add_pronouns(self, ctx, pronouns=""):
        



def setup(client):
    client.add_cog(Pronouns(client))
