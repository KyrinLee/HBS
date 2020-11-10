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

