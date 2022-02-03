import os
from datetime import datetime
from time import strptime, mktime
from Session import Session, ExplanationMode, HighlightMode

def getDateTime(line):
    timestamp = line[:19]
    timeStruct = strptime(timestamp, "%m/%d/%Y-%H:%M:%S")

    return datetime.fromtimestamp(mktime(timeStruct))

startString = "Started tab timers"
changeTabString = "Processed a page change to"
createGameString = "Creating game with"
studyOverString = "DONE with task"
clickString = "click at pixel coords"
rewindString = "rewound to decision"

explChangeString = "Processed an explanation change"
stepString = "Single Stepped Move"
explHighlightString = "On Explanation, highlight shifted from"
boardHighlightString = "On board, highlight shifted from"

sttString = "Processed an explanation change to Why: Scores Through Time"
smString = "Processed an explanation change to Why: Small Multiples"
btwString = "Processed an explanation change to Why: Best-to-Worst"


os.chdir("./logs")
filenameList = os.listdir()
if ".DS_Store" in filenameList:
    filenameList.remove(".DS_Store")
filenameList.sort()
outFile = open("../outputTimelines.html", "w")

preamble = open("../preambleTimeLines.html", 'r')
outFile.writelines(preamble.readlines())
preamble.close()

variableNameList = []
for filename in filenameList:
    highlightMode = HighlightMode.NO_HIGHLIGHT
    explanationMode = ExplanationMode.BTW_EXPL
    ses = Session(filename[0:-4], explanationMode)
    file = open(filename, "r")
    lines = file.readlines()
    numLines = len(lines)

    rewinding = False
    started = False
    for i in range(numLines):
        line = lines[i]
        if not started and startString in line:
            started = True
            ses.startTime = getDateTime(line)

        if not started:
            continue
        try:
            theTime = getDateTime(line)
        except:
            continue

        duration = theTime - ses.startTime
        relativeTime = int(duration.total_seconds())

        if createGameString in line:
            ses.gameCreations.append(relativeTime)

        elif changeTabString in line:
            ses.tabChanges.append(relativeTime)

        elif stepString in line:
            ses.steps.append(relativeTime)

        if rewindString in line:
            if rewinding:
                continue
            rewinding = True
            ses.slider.append([relativeTime, None])
        else:
            if rewinding:
                rewinding = False
                ses.slider[-1][1] = relativeTime


        if boardHighlightString in line:
            if highlightMode == HighlightMode.BOARD_HIGHLIGHT:
                continue
            ses.boardHighlights.append([relativeTime, None])
            if highlightMode == HighlightMode.EXPL_HIGHLIGHT:
                ses.explHighlights[-1][1] = relativeTime
            highlightMode = HighlightMode.BOARD_HIGHLIGHT

        elif explHighlightString in line:
            if highlightMode == HighlightMode.EXPL_HIGHLIGHT:
                continue
            ses.explHighlights.append([relativeTime, None])
            if highlightMode == HighlightMode.BOARD_HIGHLIGHT:
                ses.boardHighlights[-1][1] = relativeTime
            highlightMode = HighlightMode.EXPL_HIGHLIGHT
        elif clickString in line: #FIXME other things here?
            continue
        else:
            if highlightMode == HighlightMode.EXPL_HIGHLIGHT:
                ses.explHighlights[-1][1] = relativeTime
            elif highlightMode == HighlightMode.BOARD_HIGHLIGHT:
                ses.boardHighlights[-1][1] = relativeTime
            highlightMode = HighlightMode.NO_HIGHLIGHT


        if sttString in line:
            if explanationMode == ExplanationMode.STT_EXPL:
                continue
            ses.STTexpl.append([relativeTime, None])
            if explanationMode == ExplanationMode.SM_EXPL:
                ses.SMexpl[-1][1] = relativeTime
            elif explanationMode == ExplanationMode.BTW_EXPL:
                ses.BTWexpl[-1][1] = relativeTime
            explanationMode = ExplanationMode.STT_EXPL

        elif smString in line:
            if explanationMode == ExplanationMode.SM_EXPL:
                continue
            ses.SMexpl.append([relativeTime, None])
            if explanationMode == ExplanationMode.STT_EXPL:
                ses.STTexpl[-1][1] = relativeTime
            elif explanationMode == ExplanationMode.BTW_EXPL:
                ses.BTWexpl[-1][1] = relativeTime
            explanationMode = ExplanationMode.SM_EXPL
        elif btwString in line:
            if explanationMode == ExplanationMode.BTW_EXPL:
                continue
            ses.BTWexpl.append([relativeTime, None])
            if explanationMode == ExplanationMode.SM_EXPL:
                ses.SMexpl[-1][1] = relativeTime
            elif explanationMode == ExplanationMode.STT_EXPL:
                ses.STTexpl[-1][1] = relativeTime
            explanationMode = ExplanationMode.BTW_EXPL

        if studyOverString in line:
            ses.end(explanationMode, highlightMode, rewinding, relativeTime, duration)
            break

    file.close()

    outFile.write(str(ses))
    variableNameList.append("data" +filename[0:-4])

# Now we are outside the loop, write the postamble that catches all the variables the main loop just wrote out to the file
for i in range(len(variableNameList)):
    varName = variableNameList[i]
    outLine = "var svg" + str(i+1) + " = d3.select(\"#timeline" + str(i+1) + "\").append(\"svg\").attr(\"width\", 1200).datum(" + varName + ").call(chart);\n"
    outFile.writelines(outLine)

outLine = "\n}\n</script>\n</head>\n<body>\n"
outFile.writelines(outLine)

for i in range(len(variableNameList)):
    outLine = "<div id=\"timeline" + str(i+1) + "\"></div>\n"
    outFile.writelines(outLine)

outLine = "</body>\n</html>"
outFile.writelines(outLine)
