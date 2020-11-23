import re
import sys

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
    
    return str(num).rstrip('0').rstrip('.') + numAbbrs[power]
