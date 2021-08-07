"""
Credit Amadea Sys
"""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional, Dict, List
from datetime import date, datetime

import discord
from discord.ext import commands

import aiohttp


log = logging.getLogger(__name__)

base_url = "https://api.pluralkit.me/v1"
# --- Web Methods --- #


async def api_get(session: aiohttp.ClientSession, url: str, authorization = None):
    headers = None
    if authorization:
        headers = { 'Authorization' : authorization }
    async with session.get(f"{base_url}{url}", headers=headers) as resp:
        if resp.status == 404:
            raise NotFound
        elif resp.status == 403:
            raise Unauthorized
        json = await resp.json()
    return json


# --- Classes --- #

class Members:
    members: List[Member]

    def __init__(self, members: List[Member]):
        self.members = members

    def __repr__(self):
        return f"<Members Members={self.members}"

    def __str__(self):
        return f"<Members Members={self.members}"

    def __setitem__(self, index, value):
        self.members[index] = value

    def __getitem__(self, index):
        return self.members[index]

    def __len__(self):
        return len(self.members)

    def __iter__(self):
        ''' Returns the Iterator object '''
        return iter(self.members)

    def append(self, item):
        self.members.append(item)

    def remove(self, item):
        self.members.remove(item)

    @staticmethod
    async def get_by_hid(session: aiohttp.ClientSession, hid: str, authorization=None):
        json = await api_get(session, f"/s/{hid}/members", authorization)
        members = json

        return Members([Member(**member) for member in members])


class Fronters:
    timestamp: datetime
    members: List[Member]


    def __init__(self, timestamp, members):
        self.timestamp = timestamp
        self.members = [Member(**member) for member in members]  # Todo: replace with Members Object


    def __repr__(self):
        return f"<Fronters timestamp={self.timestamp} members={self.members}"


    def __str__(self):
        return f"<Fronters timestamp={self.timestamp} members={self.members}"


    @staticmethod
    async def get_by_hid(session: aiohttp.ClientSession, hid: str, authorization=None):
        json = await api_get(session, f"/s/{hid}/fronters", authorization)
        fronters = json
        return Fronters(**fronters)


class System:
    hid: str
    name: str
    description: str
    tag: str
    avatar_url: str
    banner: str
    created: str
    tz: str
    api_token: str
    description_privacy: Optional[str]
    member_list_privacy: Optional[str]
    front_privacy: Optional[str]
    front_history_privacy: Optional[str]


    def __init__(self, id, created, name=None, description=None, tag=None, avatar_url=None, banner=None, tz=None, api_token=None,
                 description_privacy=None, member_list_privacy=None, front_privacy=None, front_history_privacy=None):
        self.hid = id
        self.created = created
        self.name = name
        self.description = description
        self.tag = tag
        self.avatar_url = avatar_url
        self.banner = banner
        self.tz = tz
        self.api_token = api_token
        self.description_privacy = description_privacy
        self.member_list_privacy = member_list_privacy
        self.front_privacy = front_privacy
        self.front_history_privacy = front_history_privacy


    def __repr__(self):
        return f"<System hid={self.hid} name={self.name} description={self.description} tag={self.tag} avatar_url={self.avatar_url} banner={self.banner} created={self.created} tz={self.tz}"


    def __str__(self):
        return f"<System hid={self.hid} name={self.name} description={self.description} tag={self.tag} avatar_url={self.avatar_url} banner={self.banner} created={self.created} tz={self.tz}"


    async def members(self, session: aiohttp.ClientSession):
        json = await api_get(session, f"/s/{self.hid}/members", self.api_token)
        members = json
        m = []
        for member in members:
            m.append(Member(**member))
        return m


    async def fronters(self, session: aiohttp.ClientSession):
        json = await api_get(session, f"/s/{self.hid}/fronters", self.api_token)
        fronters = json
        return Fronters(**fronters)


    @staticmethod
    async def get_by_hid(session: aiohttp.ClientSession, hid, authorization=None):
        json = await api_get(session, f"/s/{hid}", authorization)
        sys = json
        return System(api_token = authorization, **sys)


    @staticmethod
    async def get_by_account(session: aiohttp.ClientSession, account, authorization=None):
        json = await api_get(session, f"/a/{account}", authorization)
        sys = json
        return System(**sys)


class ProxyTag:
    prefix: str
    suffix: str


    def __init__(self, prefix=None, suffix=None):
        if prefix is None and suffix is None:
            raise NoProxyError
        else:
            self.prefix = prefix
            self.suffix = suffix


    def __repr__(self):
        return f"<ProxyTag prefix={self.prefix} suffix={self.suffix}"


    def __str__(self):
        return f"<ProxyTag prefix={self.prefix} suffix={self.suffix}"


class Member:
    hid: str
    name: str
    display_name: str
    system: int
    color: str
    avatar_url: str
    banner: str
    birthday: date
    pronouns: str
    description: str
    proxy_tags: List
    keep_proxy: bool
    prefix: str
    suffix: str
    created: datetime
    sid: str
    privacy: Optional[str]
    visibility: str
    name_privacy: str
    description_privacy: str
    avatar_privacy: str
    birthday_privacy: str
    pronoun_privacy: str
    metadata_privacy: str

    def __init__(self, keep_proxy=None, proxy_tags=None, id=None, name=None, display_name=None, system=None, created=None, color=None,
                 avatar_url=None, banner=None, birthday=None, pronouns=None, description=None, prefix=None, suffix=None, sid=None, visibility=None, privacy=None, name_privacy=None,
                 description_privacy=None, avatar_privacy=None, birthday_privacy=None, pronoun_privacy=None, metadata_privacy=None):
        self.hid = id
        self.name = name
        self.display_name = display_name
        self.system = system
        self.created = created
        self.color = color
        self.avatar_url = avatar_url
        self.banner = banner
        self.birthday = birthday
        self.pronouns = pronouns
        self.description = description
        self.prefix = prefix
        self.suffix = suffix
        self.proxy_tags = []
        self.keep_proxy = keep_proxy
        self.sid = sid
        self.visibility = visibility
        self.privacy = privacy
        self.name_privacy = name_privacy
        self.description_privacy = description_privacy
        self.avatar_privacy = avatar_privacy
        self.birthday_privacy = birthday_privacy
        self.pronoun_privacy = pronoun_privacy
        self.metadata_privacy = metadata_privacy
        
        if proxy_tags is not None:
            for proxy_tag in proxy_tags:
                self.proxy_tags.append(ProxyTag(proxy_tag['prefix'], proxy_tag['suffix']))

    def __repr__(self):
        return f"<Member hid={self.hid} name={self.name} display_name={self.display_name} system={self.system} created={self.created} color={self.color} avatar_url={self.avatar_url} banner={self.banner_url} birthday={self.birthday} pronouns={self.pronouns} description={self.description} prefix={self.prefix} suffix={self.suffix} proxy_tags={self.proxy_tags} keep_proxy={self.keep_proxy}"

    def __str__(self):
        return f"<Member hid={self.hid} name={self.name} display_name={self.display_name} system={self.system} created={self.created} color={self.color} avatar_url={self.avatar_url} banner={self.banner_url} birthday={self.birthday} pronouns={self.pronouns} description={self.description} prefix={self.prefix} suffix={self.suffix} proxy_tags={self.proxy_tags} keep_proxy={self.keep_proxy}"

    # TODO: Determine if lazily compairing just the id's is enough or if we need to compare other vars as well
    def __eq__(self, other):
        if isinstance(other, Member):
            if self.hid == other.hid:
                return True
        return False

    @property
    def proxied_name(self):
        return self.display_name or self.name

    @staticmethod
    async def get_by_hid(session: aiohttp.ClientSession, hid, authorization = None):
        json = await api_get(session, f"/m/{hid}")
        member = json
        return Member(**member)

# --- Exceptions --- #


class PluralKitError(Exception):
    pass

class APIError(PluralKitError):
    pass

class NotFound(APIError):
    pass

class Unauthorized(APIError):
    pass

class NeedsAuthorization(APIError):
    pass

class NoProxyError(PluralKitError):
    pass
