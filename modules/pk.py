"""
Functions for interfacing with the Plural Kit API.
API Endpoint functions include:
    get_pk_system_from_userid -> /a/
    get_pk_message -> /msg/
Part of the Gabby Gums Discord Logger. (Amadea System)
"""
import discord
from discord.ext import commands
import logging
from typing import Optional, Dict

import modules.pluralKit as pk

import aiohttp


log = logging.getLogger(__name__)


class CouldNotConnectToPKAPI(Exception):
    pass

class PkApi503Error(Exception):
    pass

class UnknownPKError(Exception):
    pass

class MemberListHidden(Exception):
    pass
    
async def prompt_for_pk_token(client, ctx: commands.Context):
    user: discord.Member = ctx.author

    await user.send("Due to your Plural Kit privacy settings, I am unable to get a list of your system members.\n"
                          "As such, I require your Plural Kit system token. "
                          "Since you are obviously concerned about your systems privacy, "
                          "let me reassure you that all of your private information will be kept private and that none of your details will ever be shared with anyone else or looked at by the developer of this bot.\n"
                          "You may retrieve your system token by DMing <@!466378653216014359> with the command: `pk;token`\n"
                          "Once you have done so, please send that token to me via DM. And remember, never post your system token in a public channel!")

    def check(message):
        return message.channel.type == discord.ChannelType.private and message.author == ctx.author
    

    msg = ""
    while len(msg) != 64:
        try:
            msg = await client.wait_for('message', timeout = 300, check=check)
        except asyncio.TimeoutError:
            await ctx.send("Command has timed out. Please retry the original command")
            return 
        msg = msg.content
        if len(msg) != 64:
            await user.send("Invalid token. Please try again.")

    return msg

async def get_system_by_discord_id(discord_user_id: int) -> pk.System:
    try:
        async with aiohttp.ClientSession() as session:
            system = await pk.System.get_by_account(session, discord_user_id)
            return system
    except aiohttp.ClientError as e:
        log.warning(
            "Could not connect to PK server without errors. \n{}".format(e))

async def get_system_members_by_discord_id(discord_user_id: int) -> Optional[Dict]:
    try:
        async with aiohttp.ClientSession() as session:
            system = await pk.System.get_by_account(session, discord_user_id)
            system_members = await system.members(session)
            return system_members

    except aiohttp.ClientError as e:
        log.warning(
            "Could not connect to PK server without errors. \n{}".format(e))

async def get_pk_message(message_id: int) -> Optional[Dict]:
    """Attempts to retrieve details on a proxied/pre-proxied message"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.pluralkit.me/v1/msg/{}'.format(message_id)) as r:
                if r.status == 200:  # We received a valid response from the PK API. The message is probably a pre-proxied message.
                    logging.debug(f"Message {message_id} is still on the PK api.")
                    # Convert the JSON response to a dict, Cache the details of the proxied message, and then bail.
                    pk_response = await r.json()
                    return pk_response
                elif r.status == 404:
                    # msg was not a proxied message
                    return None
                else:
                    raise UnknownPKError(f"Received Status Code: {r.status} ({r.reason}) for /msg/{message_id}")

    except aiohttp.ClientError as e:
        raise CouldNotConnectToPKAPI
