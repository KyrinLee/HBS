import discord
import logging
import re
import json

from discord.ext import commands
import os
from replit import db
import pluralKit as pk

import sys

from dotenv import load_dotenv
load_dotenv()

import mysql.connector  

mydb = mysql.connector.connect(
     user=os.getenv("USER"), password=os.getenv("PWD"),
     host=os.getenv("HOST"), port="5432",
     database=os.getenv("DBNAME"))

mycursor = mydb.cursor()

mycursor.execute("CREATE TABLE emoji (name VARCHAR(30), id VARCHAR(30))")

mycursor.execute("SELECT * FROM emoji")

myresult = mycursor.fetchall()

for x in myresult:
	print(x)

sys.stdout.flush()
mycursor.execute("INSERT INTO emoji (emojiID, emojiUsage) VALUES (1,1)")

mydb.commit()

#print(mycursor.rowcount, "record inserted.")


client = commands.Bot(
    command_prefix="hbs;", owner_id=707112913722277899, case_insensitive=True)


# ----- Discord Events ----- #
@client.event
async def on_ready():
	sys.stdout('We have logged in as {0.user}'.format(client))
	await client.change_presence(activity=discord.Game(name='Sburb'))


def splitLongMsg(txt, limit):
	txtArr = txt.split('\n')

	output = ""
	outputArr = []

	for i in range(0, len(txtArr)):
		outputTest = output + txtArr[i] + "\n"
		if len(outputTest) > limit:
			outputArr.append(output)
			print(output)
			output = txtArr[i] + "\n"
		else:
			output = output + txtArr[i] + "\n"

	outputArr.append(output)
	return outputArr


@client.event
async def on_message(message: discord.Message):
	if message.author.id != client.user.id and message.author.id == 480855402289037312 and (
	    message.content == "<:vriska:480855644388458497>"
	    or message.content == ":vriska:" or message.content == ":eye:"):
		await message.delete()

	emojis = re.findall(r'<:\w*:\d*>', message.content)
	emojisA = re.findall(r'<a:\w*:\d*>', message.content)

	for i in range(0, len(emojisA)):
		emojis.append(emojisA[i])
	#print(emojis)
	emojiIDs = []

	for i in range(0, len(emojis)):
		emojiIDs.append(emojis[i].split(":")[2].replace('>', ''))

	updateEmojiList(message)

	if (message.author.id != 753345733377261650):
		if message.webhook_id is None:
			for e in emojiIDs:
				if e in db.keys():
					#print(db[e])
					db[e] = str(int(db[e]) + 1)
					#print(db[e])
		#print(db[e])

	#emojis = [discord.utils.get(client.get_all_emojis(), id=e) for e in emojis]

	# From now, `custom_emojis` is `list` of `discord.Emoji` that `msg` contains.

	await client.process_commands(message)


'''@client.command(pass_context=True)
async def sendEmoji(ctx, id):
  if (ctx.author.id == client.owner_id):
    await ctx.send(str(client.get_emoji(id)))
'''


@client.command(pass_context=True)
async def getEmojiUsage(ctx, num=None):
	if num == None:
		num = 10
	num = int(num)
	names = []
	counts = []
	output = ""

	i = 0
	for key in db.keys():
		names.append(key)
		counts.append(int(db[key]))

	top = [x for _, x in sorted(zip(counts, names))]

	output += "Top " + str(num) + " Emojis: "

	top.reverse()
	for i in range(0, num):
		output += str(client.get_emoji(int(top[i])))
	output += "\n\nBottom " + str(num) + " Emojis: "

	top.reverse()
	for i in range(0, num):
		output += str(client.get_emoji(int(top[i])))

	await ctx.send(output)


@client.command(pass_context=True)
async def getFullEmojiUsage(ctx):
	output = ""
	names = []
	counts = []
	i = 0

	for key in db.keys():
		names.append(key)
		counts.append(int(db[key]))
		i = i + 1

	top = [x for _, x in sorted(zip(counts, names))]

	print(top)

	for k in reversed(top):
		#print(k)
		#print(str(client.get_emoji(int(k))) + ": " + str(db[k]) + "\n")
		output += str(client.get_emoji(int(k))) + ": " + str(db[k]) + "\n"
		#print(output)

	if len(output) <= 1990:
		await ctx.send(output)

	for msg in splitLongMsg(output, 1990):
		if not msg.isspace():
			print(msg)
			await ctx.send(msg)


@client.event
async def on_raw_reaction_add(payload):
	if payload.emoji.name == "❌":
		result = -1
		channel = client.get_channel(payload.channel_id)
		msg = await channel.fetch_message(payload.message_id)
		sys = await pk.get_pk_system_from_userid(payload.user_id)
		sys = sys["id"]

		isMenu = False

		reacts = msg.reactions
		for react in reacts:
			if react.emoji == "✅":
				users = await react.users().flatten()
				for user in users:
					if user.id == 466378653216014359:
						isMenu = True

		if msg.author.id == 466378653216014359 and (not isMenu):
			for embed in msg.embeds:
				emb = json.dumps(embed.to_dict())
				if (emb.find(sys) != -1):
					result = 1
			if result == 1:
				await msg.edit(suppress=True)
				await msg.clear_reactions()
				msgDel = client.get_emoji(767960168444723210)
				await msg.add_reaction(msgDel)
		#await channel.send("message deleted")

	if payload.emoji.name == "❌" and msg.author.id == 480855402289037312:
		await msg.delete()

	if (str(payload.emoji.id) in db.keys()):
		db[str(payload.emoji.id)] = str(int(db[str(payload.emoji.id)]) + 1)


@client.command()
async def getWebhooks(ctx):
	if (ctx.author.id == client.owner_id):
		content = "\n".join(
		    [f"{w.name} - {w.url}" for w in await ctx.guild.webhooks()])
		print(content)


@client.command(pass_context=True)
async def emojiUsage(ctx):
	emojis = ctx.guild.emojis

	emojiA = []
	emojiID = []
	emojiNames = []

	i = 0
	for emoji in emojis:
		emojiA.append(emoji.animated)
		emojiNames.append(emoji.name)
		emojiID.append(str(emoji.id))

		#db[emojiID] = "0";
		i += 1
	print(emojiNames)

	i = 0
	output = ""
	length = 0

	for i in range(0, len(emojiID)):
		if emojiA[i]:
			output += "<a:"
			length += 3
		else:
			output += "<:"
			length += 2
		output += emojiNames[i]
		length += len(emojiNames[i])
		output += ":"
		output += emojiID[i]
		length += len(emojiID[i]) + 1
		output += ">\n"
		length += 3

		if (length > 1900):
			#await ctx.send(output)
			output = ""
			length = 0


@client.command(pass_context=True)
async def botnick(ctx, *, name):
	if ctx.message.author.id == 707112913722277899:
		await ctx.guild.me.edit(nick=name)


def updateEmojiList(message):
	emojis = message.guild.emojis
	newEmojis = []

	i = 0
	for emoji in emojis:
		newEmojis.append(str(emoji.id))

		i += 1

	oldEmojis = db.keys()

	tbd = list(sorted(set(oldEmojis) - set(newEmojis)))
	tba = list(sorted(set(newEmojis) - set(oldEmojis)))

	delCount = 0
	addCount = 0

	for emoji in tbd:
		del db[emoji]
		delCount += 1
	for emoji in tba:
		db[emoji] = "0"
		addCount += 1

	#output = str(delCount) + " emojis deleted\n" + str(addCount) + " emojis added"
	#await message.channel.send(output)


@client.command(pass_context=True)
async def updateEmojis(ctx):
	emojis = ctx.guild.emojis
	newEmojis = []

	i = 0
	for emoji in emojis:
		newEmojis.append(str(emoji.id))

		i += 1

	oldEmojis = db.keys()

	tbd = list(sorted(set(oldEmojis) - set(newEmojis)))
	tba = list(sorted(set(newEmojis) - set(oldEmojis)))

	delCount = 0
	addCount = 0

	for emoji in tbd:
		del db[emoji]
		delCount += 1
	for emoji in tba:
		db[emoji] = "0"
		addCount += 1

	output = str(delCount) + " emojis deleted\n" + str(
	    addCount) + " emojis added"
	await ctx.send(output)


@client.command(pass_context=True)
async def clearEmojiList(ctx):
	if ctx.message.author.id == 707112913722277899:
		keys = db.keys()
		for key in keys:
			del db[key]
		await ctx.send("Emoji list cleared.")
	else:
		await ctx.send("You do not have the permissions for this command.")


@client.event
async def on_error(event_name, *args):
	logging.exception("Exception from event {}".format(event_name))

client.run(os.getenv("TOKEN"))
