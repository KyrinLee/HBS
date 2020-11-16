import re
import sys

def splitLongMsg(txt, limit=1990):
    txtArr = txt.split('\n')

    output = ""
    outputArr = []

    for i in range(0, len(txtArr)):
        outputTest = output + txtArr[i] + "\n"
        if len(outputTest) > limit:
            outputArr.append(output)
            #print(output)
            output = txtArr[i] + "\n"
        else:
            output = output + txtArr[i] + "\n"

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
