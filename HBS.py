import discord
import logging
import re
import json

from discord.ext import commands
import os

import pk

import sys

import os
import psycopg2

from psycopg2 import Error

global delCount
global addCount

DATABASE_URL = os.environ['DATABASE_URL']

client = commands.Bot(
    command_prefix="hbs;", owner_id=707112913722277899, case_insensitive=True)


# ----- Discord Events ----- #
@client.event
async def on_ready():
    #await client.get_channel(753349219808444438).send("We have logged in")
    sys.stdout.write("We have logged in.")
    await client.change_presence(activity=discord.Game(name='Sburb'))


def splitLongMsg(txt, limit=1990):
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

#HANDLE HUSSIEBOT VRISKA REACTS
    if message.author.id != client.user.id and message.author.id == 480855402289037312:
                if (message.content == "<:vriska:480855644388458497>" or message.content == ":vriska:" or message.content == ":eye:"):
                        await message.delete()

#EMOJI HANDLING

    connection = psycopg2.connect(DATABASE_URL, sslmode='require')

    cursor = connection.cursor()
    postgreSQL_select_Query = "SELECT id FROM emoji"
    update_q = "UPDATE emoji SET usage = %s WHERE id = %s"
    get_usage = "SELECT usage FROM emoji WHERE id=%s"

    cursor.execute(postgreSQL_select_Query)
    oldEmojis = cursor.fetchall()

    oldEmojis = [e[0] for e in oldEmojis]

    emojis = re.findall(r'<:\w*:\d*>', message.content)
    emojisA = re.findall(r'<a:\w*:\d*>', message.content)

    for i in range(0, len(emojisA)):
        emojis.append(emojisA[i])
    #print(emojis)
    emojiIDs = []

    for i in range(0, len(emojis)):
        emojiIDs.append(emojis[i].split(":")[2].replace('>', ''))

    updateEmojiList(message)

    if message.author.id != 753345733377261650 and message.webhook_id is None:
        for e in emojiIDs:
            if e in oldEmojis:
                    cursor.execute(get_usage,(e,))
                    use = cursor.fetchall()
                    cursor.execute(update_q, (use[0][0]+1,e))
                    #if message.channel.id == 754527915290525807:
                    #        await client.get_channel(754527915290525807).send(str(use[0]))
                                
    connection.commit()                            
    cursor.close()
    connection.close()
    await client.process_commands(message)


'''@client.command(pass_context=True)
async def sendEmoji(ctx, id):
  if (ctx.author.id == client.owner_id):
    await ctx.send(str(client.get_emoji(id)))
'''


@client.command(pass_context=True)
async def getEmojiUsage(ctx, num=None, animated=None):
        if num == None:
                num = 15

        connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = connection.cursor()

        if animated == "-s":
                cursor.execute("SELECT * FROM emoji WHERE animated = FALSE ORDER BY usage DESC")
        elif animated == "-a":
                cursor.execute("SELECT * FROM emoji WHERE animated = TRUE ORDER BY usage DESC")
        else:
                cursor.execute("SELECT * FROM emoji ORDER BY usage DESC")

        emojis = cursor.fetchall()
        output = "Top " + str(num) + " emojis: "

        for i in range(0,num):
                output += str(client.get_emoji(int(emojis[i][1])))
        output += "\nBottom " + str(num) + " emojis: "

        for i in range(len(emojis)-1,len(emojis)-1-num,-1):
                output += str(client.get_emoji(int(emojis[i][1])))

                
        if animated == "-s":
                output+="\n(animated emojis excluded.)"
        if animated == "-a":
                output+="\n(static emojis excluded.)"
        await ctx.send(output)


@client.command(pass_context=True)
async def getFullEmojiUsage(ctx):
        
        connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM emoji")

        data = cursor.fetchall()

        output = ""
        for i in data:
                output += str(client.get_emoji(int(i[1]))) + ": " + str(i[3]) + "\n"
                
        outputArr = splitLongMsg(output)
        for o in outputArr:
                await ctx.send(o)

        connection.commit()
        cursor.close()
        connection.close()
        
@client.event
async def on_raw_reaction_add(payload):
    '''if payload.emoji.name == "❌":
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

'''
@client.command()
async def getWebhooks(ctx):
    if (ctx.author.id == client.owner_id):
        content = "\n".join(
            [f"{w.name} - {w.url}" for w in await ctx.guild.webhooks()])
        print(content)


'''@client.command(pass_context=True)
async def emojiUsage(ctx):
        connection =psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM emoji ORDER BY id::int")

        emojis = cursor.fetchall()

        for (
'''
@client.command(pass_context=True)
async def botnick(ctx, *, name):
    if ctx.message.author.id == 707112913722277899:
        await ctx.guild.me.edit(nick=name)


def updateEmojiList(message):
        
        connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = connection.cursor()
        
        sql_insert_query = """ INSERT INTO emoji (name, id, animated, usage) VALUES (%s,%s,%s,%s)"""
        sql_delete_query = """ DELETE FROM emoji WHERE id = %s """
        
        emojis = message.guild.emojis
        newEmojis = []

        i = 0
        for emoji in emojis:
                        newEmojis.append(str(emoji.id))
                        i+=1

        postgreSQL_select_Query = "SELECT * FROM emoji"

        cursor.execute(postgreSQL_select_Query)
        tempEmojis = cursor.fetchall()

        oldEmojis = []
        for e in tempEmojis:
                oldEmojis.append(e[1])
        
        tbd = list(sorted(set(oldEmojis) - set(newEmojis)))
        tba = list(sorted(set(newEmojis) - set(oldEmojis)))

        delCount = 0
        addCount = 0

        for emoji in tbd:
                cursor.execute(sql_delete_query, (emoji,))
                delCount += 1

        for emoji in tba:
                e = client.get_emoji(int(emoji))
                record_to_insert = (e.name, str(e.id), e.animated, 0)
                cursor.execute(sql_insert_query, record_to_insert)
                addCount = addCount + 1

        connection.commit()
        cursor.close()
        connection.close()
        
@client.command(pass_context=True)
async def updateEmojis(ctx):

        updateEmojiList(ctx.message)
        await ctx.send("Emoji List Updated.")
        

@client.command(pass_context=True)
async def clearEmojiList(ctx):
        connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = connection.cursor()

        if ctx.message.author.id == 707112913722277899:
                delete_query = "DELETE FROM emoji"
                cursor.execute(delete_query)
                connection.commit()
                await ctx.send("Emoji list cleared.")

        else:
                await ctx.send("You do not have the permissions for this command.")

        connection.commit()
        cursor.close()
        connection.close()

@client.command(pass_context=True)
async def addEmoji(ctx,id):
        connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        cursor = connection.cursor()
        sql_insert_query = """ INSERT INTO emoji (name, id, animated, usage) VALUES (%s,%s,%s,%s)"""
        emoji = client.get_emoji(int(id))
        
        emojiData = (emoji.name,emoji.id,emoji.animated,0)
        try:
                cursor.execute(sql_insert_query, emojiData)
                #await ctx.send("Emoji added.")
                cursor.execute("SELECT * FROM emoji WHERE id = %s", (str(id),))
                await ctx.send(cursor.fetchall())

        except:
                "Emoji addition failed."

        cursor.close()
        connection.close()

@client.command(pass_context=True)
async def createEmojiTable(ctx):

        connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        try:
    
                cursor = connection.cursor()
                
                create_table_query = '''CREATE TABLE emoji
                          (name VARCHAR(30),
                         id VARCHAR(30),
                         animated BOOLEAN,
                         usage INT); '''
                
                cursor.execute(create_table_query)
                connection.commit()
                print("Table created successfully in PostgreSQL ")

        except (Exception, psycopg2.DatabaseError) as error :
                print ("Error while creating PostgreSQL table", error)


        finally:
                #closing database connection.
                        if(connection):
                                cursor.close()
                                connection.close()
                                print("PostgreSQL connection is closed")

@client.command(pass_context=True)
async def dump(ctx):
        if ctx.author.id == 707112913722277899:
                connection = psycopg2.connect(DATABASE_URL, sslmode='require')
                cursor = connection.cursor()

                cursor.execute("SELECT * FROM emoji")
                data = cursor.fetchall()

                await ctx.send(data)
                        
                cursor.close()
                connection.close()


@client.event
async def on_error(event_name, *args):
    logging.exception("Exception from event {}".format(event_name))

client.run(os.environ["token"])

