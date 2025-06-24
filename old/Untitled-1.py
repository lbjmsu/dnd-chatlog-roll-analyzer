allOfHistory = ""
with open(".\\Untitled-1.html") as f:
    #allOfHistory = f.read()
    a = 0
    for line in f:
        a += 1
        allOfHistory += line
    print(a)

def processRolls(div: str):
    #   Split items into "tag elementContent" and "/tag"
    #   Almost all important content follows opening tags
    items = list(map(lambda x: x.strip(), " ".join(div.split(">")).split("<") ))

    stack = []
    rolls = []

    rollInformation = {"dice":[]}
    currDie = ""

    nonRoll = False

    for i in items:
        #print(stack)
        if not stack:
            if nonRoll:
                nonRoll = False
            else:
                if rollInformation["dice"]:
                    #print(rollInformation)
                    rolls.append(rollInformation)
                if "by" in rollInformation:
                    rollInformation = {"dice":[], "by":rollInformation["by"]}
                else:
                    rollInformation = {"dice":[]}
        if not i:
            continue
        if i[0] == "/":
            stack.pop()
        else:
            if i.split()[0] == "img":
                continue

            stack.append(i)
            if nonRoll:
                continue

            #   Compartmentalize html into attributes
            #   Look for class: if "tstamp", "by", or "inlinerollresult"
            
            #   "try" should be replaced with a more robust way to handle erroneous rolls or rolls originating from the character sheet, but these are the minority of rolls, so they are skipped.
            try:
                attrs = {}
                resList = []
                curWord = ""
                inQuotes = False

                #   Separate HTML string into words
                for iter in range(len(i)):
                    character = i[iter]
                    if not inQuotes:
                        if character == " ":
                            resList.append(curWord)
                            curWord = ""
                        elif character == "\"":
                            inQuotes = True
                        else:
                            curWord += character
                    else:
                        if character == "\"":
                            inQuotes = False
                            iter += 1
                            key, value = curWord.split("=")
                            attrs[key] = value
                            curWord = ""
                        else:
                            curWord += character
                resList.append(curWord)

                # print(i)
                # print(attrs)
                # print(resList)
                

                #   Process information based on class
                if "class" in attrs:
                    if "diceroll" in attrs["class"]:
                        if attrs["class"].split()[1] == "withouticons":
                            currDie = attrs["class"].split()[2]
                        else:
                            currDie = attrs["class"].split()[1]

                        if currDie not in rollInformation["dice"]:
                            rollInformation["dice"].append(currDie)
                    
                    elif attrs["class"] == "formula":
                        rollInformation["formula"] = resList[-1]
                    elif attrs["class"] == "didroll":
                        if currDie in rollInformation:
                            rollInformation[currDie].append(int(resList[-1]))
                        else:
                            rollInformation[currDie] = [int(resList[-1])]
                    elif attrs["class"] == "rolled":
                        rollInformation["result"] = int(resList[-1])
                    elif attrs["class"] == "tstamp":
                        rollInformation["tstamp"] = " ".join(resList[1:]).strip()[:-1]
                        print(rollInformation["tstamp"])
                    elif attrs["class"] == "by":
                        rollInformation["by"] = " ".join(resList[1:]).strip()[:-1]
                    #print(rollInformation)

            except :
                nonRoll = True
            
    #print(rollInformation)
    #rolls.append(rollInformation)
    #print(stack)

    return rolls

def getRolls(jsonRolls, player="", dieType=""):
    playerRolls = {}
    rolls = {}
    if player == "":
        for r in jsonRolls:
            for dieType in r["dice"]:
                for roll in r[dieType]:
                    if r["by"] not in playerRolls:
                        playerRolls[r["by"]] = {}
                    if dieType in playerRolls[r["by"]]:
                        playerRolls[r["by"]][dieType].append(roll)
                    else:
                        playerRolls[r["by"]][dieType] = [roll]
        return playerRolls
    if dieType == "":
        playerRolls = list(filter(lambda x: x["by"] == player, jsonRolls))
        for r in playerRolls:
            for dieType in r["dice"]:
                for roll in r[dieType]:
                    if dieType in rolls:
                        rolls[dieType].append(roll)
                    else:
                        rolls[dieType] = [roll]
    else:
        filteredRolls = list(filter(lambda x: x["by"] == player and dieType in x["dice"], jsonRolls))
        for r in filteredRolls:
            for roll in r[dieType]:
                if dieType in rolls:
                    rolls[dieType].append(roll)
                else:
                    rolls[dieType] = [roll]
    
    return rolls

rolls = processRolls(allOfHistory)
print(rolls)
rollsByPersonDie = getRolls(rolls, "nimmexx")
print(rollsByPersonDie)
#   For each person
#   For each roll type
#       Print number of rolls
#       Print average value
for person in rollsByPersonDie:
    print(person)
    # for dieType in rollsByPersonDie[person]:
    #     print(dieType)
    #     print(rollsByPersonDie[person][dieType])
#print(rolls)
# brocasRolls = getRolls(rolls, "Brocas")
# print(brocasRolls)
# brocasD20Rolls = brocasRolls["d20"]
# print(len(brocasD20Rolls))
# print(sum(brocasD20Rolls)/len(brocasD20Rolls))

