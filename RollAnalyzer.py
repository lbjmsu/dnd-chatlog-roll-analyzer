from collections import defaultdict

# -------------------------------------------------------------------------------------------------------
#       INITIAL NOTES:
#           1. IMPORTANT USER INFORMATION -- See "USER SECTION" at bottom of this file for simplified usage and data analysis.
#           2. This program has only been tested on the associated HTML file thus far. Thus, certain input validation techniques may need to be added
# -------------------------------------------------------------------------------------------------------


# -------------------------------------------------------------------------------------------------------
#       FILE PREPROCESSING SECTION:
#           Retrieve the "rolls" section of the chat log file and ensure character compatibility (i.e., replace "&lt;" and similar multi-char character representations)
# -------------------------------------------------------------------------------------------------------


#   Read all characters from the chat log html file
logContent = ""
with open("Chat Log for Eramu Full.htm", encoding="utf-8") as f:
    logContent = f.read()

#   Retrieve just the "rolls" portion of the html -- are these always the same?
start = "<div class=\"message"
end = """</div>
</div>
<script id="tmpl_chatmessage_general" type="text/html">"""

contentStart = logContent.index(start)
contentEnd = logContent.index(end)
logContent = logContent[contentStart:contentEnd]

#   Creates a problem with roll formulas that contain a "< or >", e.g., rolling {24D20+5}>14
#   TODO: 1. Create a flag to ignore everything after a class="formula" div tag until "</" is found. Requires a "prevChar" variable
logContent = logContent.replace("&lt;", "<").replace("&quot;", "\"").replace("&gt;", ">")


# -------------------------------------------------------------------------------------------------------
#       HTML PROCESSING SECTION:
#           Using a stack, iterate through all elements in the HTML file, extracting roll information such as die type, roll result, timestamp, etc. for each roll in the HTML.
# -------------------------------------------------------------------------------------------------------


def getRolls(chatLog: str, debug: bool = False):
    #   Element tracking variables
    element = ""                #   Stores the current element as it's being read
    openTagFlag = False         #   Tracks if we are currently defining a tag
    openElementFlag = True      #   Tracks if we are currently defining an element
    tag = ""
    stack = []
    elemStack = []

    rolls = []

    tstampFlag = False
    byFlag = False
    didRollFlag = False
    delayedDidRollFlag = False
    delayedRoll = 0

    roll = {"rolls":{}}
    mostRecentDie = None
    
    for char in chatLog:

        #   Opening a new tag
        if char == "<":

            #   If a set of rolls has been processed
            #       "if not stack" implies a rollset div has been fully processed and is ready to be added to output
            if not stack and mostRecentDie != None:

                #   Remove None-die rolls (incorrectly-processed character sheet rolls)
                if '' in roll["rolls"]:
                    del roll["rolls"]['']
                
                #   Remove None-result rolls (incorrectly-processed character sheet rolls?)
                temp = roll["rolls"].copy()
                for dieType in roll["rolls"]:
                    rollVals = []
                    for result in roll["rolls"][dieType]:
                        if result and result.isnumeric() and result != 0:
                            rollVals.append(result)
                    if rollVals:
                        temp[dieType] = rollVals
                    else:
                        del temp[dieType]
                roll["rolls"] = temp

                #   Add result to output if any rolls remain after cleaning the result
                if roll["rolls"]:
                    rolls.append(roll)
                
                #   Set next roll set's "by" and "timestamp" properties if found, since successive roll sets do not contain timestamp or owner information
                if "by" in roll and "timestamp" in roll:
                    roll = {"rolls":{}, "by": roll["by"], "timestamp": roll["timestamp"]}
                else:
                    roll = {"rolls":{}}

                #   Reset mostRecentDie to ensure access to this codeblock only occurs when rolls were found
                mostRecentDie = None
                if debug: print()

            #   There is an element inside this tag; Preempt that element to process this new one
            if element and openElementFlag:
                elemStack.append([element, tag, len(stack)])
            
            #   Opening a new tag; Process the text between element tags
            else:
                if tstampFlag:
                    roll["timestamp"] = element
                    if debug: print("TIMESTAMP:", element)
                    tstampFlag = False
                if byFlag:
                    roll["by"] = element[:-1]
                    if debug: print("BY:", element[:-1])
                    byFlag = False
                if didRollFlag:
                    roll["rolls"][mostRecentDie].append(element)
                    if debug: print("RESULT:", element)
                    didRollFlag = False
                if delayedDidRollFlag:
                    delayedRoll = element
                openTagFlag = True
            
            openElementFlag = True
            element = ""


        #   Define current tag for use in html-processing stack 
        elif (char == " " or char == ">") and openTagFlag:
            tag = element[1:]
            openTagFlag = False


        element += char     #   Add current character to element string

        #   Closing an element
        if char == ">":
            openElementFlag = False

            #   img and br tags don't have closing tags
            if tag == "img" or tag == "br":
                pass

            #   This tag is a closing tag
            elif tag[0] == "/":

                #   This closing tag matches the top tag on the stack (it should always be true, but this is here for validation purposes)
                if tag[1:] == stack[-1]:
                    stack.pop()     #   Pop the opening tag off the tag stack

                    #   This tag closes an element that is inside another tag
                    if elemStack and len(stack) == elemStack[-1][2]:

                        #   Restore element and tag from the elemStack to continue processing
                        element = elemStack[-1][0]
                        tag = elemStack[-1][1]
                        elemStack.pop()
                        continue
            
            #   This tag is an opening tag
            else:
                #   TODO 2.: Handle more types of rolls from the chat log
                #   TODO 3.: Remove 2dF
                #   Determine die type based on contents of the tag's attributes
                if "class=\"diceroll" in element or "title=\"Rolling" in element:
                    rollPhrasing = "title=\"Rolling" if "title=\"Rolling" in element else "class=\"diceroll"
                    index = element.index(rollPhrasing) + len(rollPhrasing) + 1     #   index of the first character in the formula
                    die = ""        #   String to store the die type
                    dFound = False  #   Boolean that stores if a "d" has been found (signifying beginning of die type)
                    for i in range(index,len(element)):
                        #   a. element[i] is in numbers before the d (e.g. **12**d20)
                        if element[i].isnumeric() and not dFound:
                            continue
                        #   b. element[i] is in numbers after the d (e.g. 12d**20**)
                        elif element[i].isnumeric(): 
                            die += element[i]
                        #   c. element[i] is the d (e.g. 12**d**20)
                        elif element[i] == "d":
                            die += element[i]
                            dFound = True
                        #   d. element[i] is non-numeric (a character after the numbers described by b.)
                        else:
                            break
                    mostRecentDie = die     #   Set the most recent die to the die that was found

                    #   If the result was found before the die that was rolled (Character Sheet rolls), add the roll result information here. Roll result handling otherwise handled above.
                    if delayedDidRollFlag:
                        if mostRecentDie in roll["rolls"]:
                            roll["rolls"][mostRecentDie].append(delayedRoll)
                        else:
                            roll["rolls"][mostRecentDie] = [delayedRoll]
                        delayedRoll = 0
                        delayedDidRollFlag = False
                    
                    #   Otherwise, guarantee that this dictionary in "rolls" is available to be added to for the main roll-adding logic above
                    else:
                        if mostRecentDie not in roll["rolls"]:
                            roll["rolls"][mostRecentDie] = []
                    if debug: print("ROLLED A:", die)
                
                #   Get roll type information
                if "\"formula\"" in element:
                    #   TODO: 1. (See above)
                    if debug: print("Basic Roll")
                elif "sheet-rolltemplate-simple" in element:
                    if debug: print("Roll from Character Sheet")

                #   Get timestamp information from next element
                if "class=\"tstamp" in element:
                    tstampFlag = True

                #   Get roll owner's information from next element
                elif "class=\"by" in element:
                    byFlag = True

                #   Get roll result information from next element
                elif "class=\"didroll" in element: 
                    didRollFlag = True
                
                elif "class=\"basicdiceroll" in element:
                    delayedDidRollFlag = True
                
                #   Add this tag to the tag stack
                stack.append(tag)
            element = ""
    
    #   Add the final processed rollset to the output
    if not stack and mostRecentDie != None:
        rolls.append(roll)

    if debug: print(len(stack))
    if debug: print(stack)

    return rolls


# -------------------------------------------------------------------------------------------------------
#       DATA SIMPLIFICATION SECTION:
#           Extract roll information (for a specific player/specific die, if requested) from the dict of "rolls" as seen in the above section
# -------------------------------------------------------------------------------------------------------


def processJsonRolls(jsonRolls, player="", dieType=""):
    #   If jsonRolls is a single json object, turn it into a list with one object (it)
    if type(jsonRolls) is not list:
        jsonRolls = [jsonRolls]

    #   Create default values for rolls["player"] -> (defaultdict(list)) and for rolls["player"]["dieType"] -> (list)
    rolls = defaultdict(lambda: defaultdict(list))

    #   Filter jsonRolls to match the user-provided arguments
    argFilter = lambda x: (x if not player else x["by"] == player) and (x if not dieType else dieType in x["rolls"])
    jsonRolls = list(filter(argFilter, jsonRolls))
    
    #   Process roll results from the list of roll sets in "jsonRolls"
    for rollSet in jsonRolls:
        rollDieTypes = [dieType] if dieType else rollSet["rolls"].keys()   #   Get list of die types rolled in the current roll set
        for dType in rollDieTypes:  
            for rollResult in rollSet["rolls"][dType]:
                rolls[rollSet["by"]][dType].append(int(rollResult))
    
    return dict(rolls)


# -------------------------------------------------------------------------------------------------------
#       USER SECTION:
#           Use this section to analyze rolls based on player and on die type (e.g., d4, d6, d8, etc.)
# -------------------------------------------------------------------------------------------------------


rolls = getRolls(logContent)
processedRolls = processJsonRolls(rolls)

#   Note: Brocas and Brocas Weldge are both Brannon. There are also two Emersons (Kasai M., Emerson J.) and two Caios (Caio S., Drott)
print("Players:", list(processedRolls.keys()))


#   Change "Caio S." in the "player" variable below to whichever character you wish to analyze:
player = "Caio S."
print(f"{player}'s roll types:", list(processedRolls[player].keys()))   #   Print a list of die types rolled by the chosen player.

#   Change the "dieType" variable to whichever die type you would like to receive results for:
dieType = "d20"

#   Print the results of your roll query!
playerRolls = processedRolls[player][dieType]
if dieType in processedRolls[player]:
    print(f"{player}'s {dieType} rolls:", playerRolls)
else:
    print(f"{player} has no {dieType} rolls.")

#   ADVANCED: Get a list of rolls of a certain die type from a player by referencing processedRolls["playerName"]["dieType"]
#       e.g. print("Emerson J.'s d10 rolls:", processedRolls["Emerson J."]["d10"])
#       e.g. print("Hannah Kuu's d4 rolls:", processedRolls["Hannah Kuu"]["d4"])
#   OR: Reference "playerRolls" to further process the rolls retrieved above.