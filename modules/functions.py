import re
import sys
from modules import checks

def splitLongMsg(txt, limit=1990,char='\n'):
    txtArr = txt.split(char)

    output = ""
    outputArr = []

    for i in range(0, len(txtArr)):
        outputTest = output + txtArr[i] + char
        if len(outputTest) > limit:
            outputArr.append(output)
            #print(output)
            output = txtArr[i] + char
        else:
            output = output + txtArr[i] + char

    outputArr.append(output)
    return outputArr


def formatTriggerDoc(txt):
    txtArr = re.split('(censor the text as well.)',txt)

    txtArr[2] = re.sub(r'\[([\s\S]*?)\]',r'||\1||',txtArr[2])
    txtArr[2] = re.sub(r'(\*\*[\s\S]*?\*\*)',r'__\1__',txtArr[2])
    txtArr[2] = re.sub(r'-        ',r'      - ',txtArr[2])
    #txtArr[2] = re.sub(r': *(.{2,}[\r\n]*)',r': ||\1||',txtArr[2])

    #txtArr[2] = re.sub(r'\* (.*[\r\n]*)',r'* ||\1||',txtArr[2])

    
    txtArr[2] = re.sub(r'\r\n\|\|',r'||\n',txtArr[2])

    return "".join(txtArr)


# ----- CONFIRMATION MENU ----- #

async def confirmationMenu(client, ctx, confirmationMessage="",autoclear=""):
    msg = await ctx.send(confirmationMessage)
  
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author

    try:
        reaction, user = await client.wait_for('reaction_add', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send("Oops too slow!")
        if autoclear: await msg.delete()
        return 0

    if user == ctx.author:
        if str(reaction) == "❌":
            if autoclear: await msg.delete()
            return 0
        elif str(reaction) == "✅":
            if autoclear: await msg.delete()
            return 1
    else:
        if autoclear: await msg.delete()
        return -1

# ----- FIND MESSAGE VIA ID OR LINK ----- #
async def getMessage(client, ctx,id=None, channelId=None):
    if id == None:
        raise checks.InvalidArgument("Please include valid message ID or link.")

    else:
        awaitMsg = await ctx.send("Retrieving message... This may take a minute.")

        if str(id)[0:4] == "http":
            link = id.split('/')
            channel_id = int(link[6])
            msg_id = int(link[5])
            msg = await client.get_channel(channel_id).fetch_message(msg_id)
        else:
            msg = []
            for channel in ctx.guild.text_channels:
                try:
                    msg.append(await channel.fetch_message(id))
                except:
                    continue
        
            if msg == []:
                await awaitMsg.delete()
                raise checks.InvalidArgument("That message does not exist.")
            elif len(msg) > 1:
                await awaitMsg.delete()
                raise checks.InvalidArgument("Multiple messages with that ID found. Please run the command again using the message link instead of the ID.")
        

        await awaitMsg.delete()
    return msg[0]



def numberFormat(num):
    numAbbrs = ["k","m","b","t"]
    
    if num < 1000:
        return num
    power = 0
    while num > 1:
        num = num / 10
        power = power + 1
    num = round(num, 3)
    
    while True:
        num = num * 10
        power = power - 1
        if power % 3 == 0:
            break

    power = power // 3 - 1
    if len(str(num)) > 5:
        num = str(num)[0:4]
    
    return str(num).rstrip('0').rstrip('.') + numAbbrs[power]
