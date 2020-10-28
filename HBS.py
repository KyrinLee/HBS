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

startup_extensions = ["dayCount"]

DATABASE_URL = os.environ['DATABASE_URL']

client = commands.Bot(
    command_prefix=("hbs;","\hbs;"),
    owner_id=707112913722277899,
    case_insensitive=True,
    help_command=None)


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

    connection = psycopg2.connect(DATABASE_URL, sslmode='require')

    cursor = connection.cursor()
    postgreSQL_select_Query = "SELECT id FROM emoji"
    update_q = "UPDATE emoji SET usage = %s WHERE id = %s"
    get_usage = "SELECT usage FROM emoji WHERE id=%s"

    cursor.execute(postgreSQL_select_Query)
    emojis = cursor.fetchall()

    emojis = [e[0] for e in emojis]

    if str(payload.emoji.id) in emojis:
        cursor.execute(get_usage,(str(payload.emoji.id),))
        use = cursor.fetchall()
        cursor.execute(update_q, (use[0][0]+1,str(payload.emoji.id)))
                                
    connection.commit()                            
    cursor.close()
    connection.close()

'''@client.command(pass_context=True)
async def sendEmoji(ctx, id):
  if (ctx.author.id == client.owner_id):
    await ctx.send(str(client.get_emoji(id)))
'''

def is_in_guild(guild_id):
    async def predicate(ctx):
        return ctx.guild and ctx.guild.id == guild_id
    return commands.check(predicate)


@client.command(pass_context=True)
async def getEmojiUsage(ctx, num=None, animated=None):
        if num == None:
                num = 15
        elif num == "-s" or num == "-a":
                animated = num
                num = 15
        else:
                num = int(num)

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
        cursor.execute("SELECT * FROM emoji ORDER BY usage DESC")

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
@is_in_guild(609112858214793217)
async def updateEmojis(ctx,description="Updates emoji list for current guild (Limited to Sky's Server.)"):

        updateEmojiList(ctx.message)
        await ctx.send("Emoji List Updated.")
        

@client.command(pass_context=True)
@commands.is_owner()
async def clearEmojiList(ctx,hidden=True,description="Clears emoji usage data."):
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
@commands.is_owner()
async def addEmoji(ctx,id,hidden=True):
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
@commands.is_owner()
async def createEmojiTable(ctx,hidden=True,description="Creates emoji table."):

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
@commands.is_owner()
async def dump(ctx, hidden=True, description="Dumps emoji table data."):
        if ctx.author.id == 707112913722277899:
                connection = psycopg2.connect(DATABASE_URL, sslmode='require')
                cursor = connection.cursor()

                cursor.execute("SELECT * FROM emoji")
                data = cursor.fetchall()

                await ctx.send(data)
                sys.stdout.write(data)
                        
                cursor.close()
                connection.close()

@client.command(pass_context=True)
async def spoil(ctx, *, text, brief="Resends image(s) under spoiler tags.", description="Resends image(s) under spoiler tags. Can send up to 10 images."):
    files = []
    for a in ctx.message.attachments:
        file = await a.to_file(use_cached=True, spoiler=True)
        files.append(file)

    ping = "Sent by <@" + str(ctx.author.id) + ">\n**" + text + "**";
    await ctx.send(content=ping, files=files)
    await ctx.message.delete()


@client.command(pass_context=True)
async def help(ctx, command=None):
    embed = discord.Embed(title="HBS Help", description="Help menu for HBS.", color=0x005682)

    embed.add_field(name="reset", value="**hbs;reset <countername>**\nResets given counter.", inline=False)
    embed.add_field(name="geu", value="**hbs;getEmojiUsage <num> <animated>**\nReturns top and bottom <num> emojis. Static or animated can be specified using -s or -a.", inline=False)
    embed.add_field(name="gfeu", value="**hbs;getFullEmojiUsage**\nReturns all emojis in server with usage stats, sorted by most to least used.", inline=False)
    embed.add_field(name="spoil", value="**hbs;spoil <text> <image(s)>, or \hbs;spoil <text> <image(s)> (to escape pk autoproxy.)**\nResends image(s) under spoiler tag, with text. Can spoil up to 10 images at once.",inline=False)

    await message.channel.send(embed=embed)

@client.command(pass_context=True)
@commands.is_owner()
async def botnick(ctx, *, name, hidden=True, description="Changes bot nickname in current guild."):
    await ctx.guild.me.edit(nick=name)

@client.command(pass_context=True)
@commands.is_owner()
async def changeGame(ctx, *, game, hidden=True, description="Changes \"currently playing\" text."):
    await client.change_presence(activity=discord.Game(name=game))

@client.event
async def on_error(event_name, *args):
    logging.exception("Exception from event {}".format(event_name))


if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            client.load_extension(extension)
        except Exception as e:
            exc = '{}: {}'.format(type(e).__name__, e)
            print('Failed to load extension {}\n{}'.format(extension, exc))
            
client.run(os.environ["token"])

