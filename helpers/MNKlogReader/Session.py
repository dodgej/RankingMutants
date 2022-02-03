from datetime import timedelta
from enum import Enum

class ExplanationMode(Enum):
    STT_EXPL = 0
    SM_EXPL  = 1
    BTW_EXPL = 2

class HighlightMode(Enum):
    BOARD_HIGHLIGHT = 0
    EXPL_HIGHLIGHT  = 1
    NO_HIGHLIGHT    = 2

class Game:
    multiplier = 1000
    def __init__(self, filename, explanationMode, gameNum):
        self.varName = filename
        self.gameNum = gameNum
        self.tabChanges = []
        self.steps = []
        self.boardHighlights = []
        self.explHighlights = []
        self.STTexpl = []
        self.SMexpl = []
        self.BTWexpl = []
        self.slider = []
        self.startTime = 0
        self.duration = 0
        if explanationMode == ExplanationMode.STT_EXPL:
            self.STTexpl.append([0, None])
        if explanationMode == ExplanationMode.SM_EXPL:
            self.SMexpl.append([0, None])
        if explanationMode == ExplanationMode.BTW_EXPL:
            self.BTWexpl.append([0, None])

    def end(self, explanationMode, highlightMode, rewinding, relativeTime, duration):
        if explanationMode == ExplanationMode.SM_EXPL:
            self.SMexpl[-1][1] = relativeTime
        elif explanationMode == ExplanationMode.STT_EXPL:
            self.STTexpl[-1][1] = relativeTime
        elif explanationMode == ExplanationMode.BTW_EXPL:
            self.BTWexpl[-1][1] = relativeTime

        if highlightMode == HighlightMode.EXPL_HIGHLIGHT:
            self.explHighlights[-1][1] = relativeTime
        elif highlightMode == HighlightMode.BOARD_HIGHLIGHT:
            self.boardHighlights[-1][1] = relativeTime

        if rewinding:
            self.slider[-1][1] = relativeTime
        self.duration = duration

    def trimToLastStep(self):
        if self.steps == []:
            lastStep = 0
        else:
            lastStep = self.steps[-1]
        self.duration = timedelta(seconds=lastStep)

        for i in range(len(self.tabChanges)):
            if self.tabChanges[i] > lastStep:
                self.tabChanges = self.tabChanges[0:i]
                break

        for i in range(len(self.boardHighlights)):
            if self.boardHighlights[i][0] > lastStep:
                self.boardHighlights = self.boardHighlights[0:i]
                break
        if len(self.boardHighlights) > 0:
            self.boardHighlights[-1][1] = min(lastStep, self.boardHighlights[-1][1])

        for i in range(len(self.explHighlights)):
            if self.explHighlights[i][0] > lastStep:
                self.explHighlights = self.explHighlights[0:i]
                break
        if len(self.explHighlights) > 0:
            self.explHighlights[-1][1] = min(lastStep, self.explHighlights[-1][1])

        for i in range(len(self.STTexpl)):
            if self.STTexpl[i][0] > lastStep:
                self.STTexpl = self.STTexpl[0:i]
                break
        if len(self.STTexpl) > 0:
            self.STTexpl[-1][1] = min(lastStep, self.STTexpl[-1][1])

        for i in range(len(self.SMexpl)):
            if self.SMexpl[i][0] > lastStep:
                self.SMexpl = self.SMexpl[0:i]
                break
        if len(self.SMexpl) > 0:
            self.SMexpl[-1][1] = min(lastStep, self.SMexpl[-1][1])

        for i in range(len(self.BTWexpl)):
            if self.BTWexpl[i][0] > lastStep:
                self.BTWexpl = self.BTWexpl[0:i]
                break
        if len(self.BTWexpl) > 0:
            self.BTWexpl[-1][1] = min(lastStep, self.BTWexpl[-1][1])

        for i in range(len(self.slider)):
            if self.slider[i][0] > lastStep:
                self.slider = self.slider[0:i]
                break
        if len(self.slider) > 0:
            self.slider[-1][1] = min(lastStep, self.slider[-1][1])


    @staticmethod
    def transformObs(obs):
        try:
            result = (obs + 8 * 60 * 60) * Game.multiplier
        except:
            return None
        return result

    @staticmethod
    def stringifyDuration(obsList, label):
        result = "\t{\n\t\tlabel:\"" + label + "\",\n"
        result += "\t\tUIcomponent:\"" + label + "\",\n"
        result += "\t\ttimes: [\n"
        duration = 0
        for obs in obsList:
            startTransformed = Game.transformObs(obs[0])
            endTransformed = Game.transformObs(obs[1])
            result += "\t\t\t{\"starting_time\": " + str(startTransformed) + ", \"ending_time\":" + str(endTransformed) + "},\n"
            duration += obs[1] - obs[0]
        result += "\t\t]\n\t},"

        durationDelta = timedelta(seconds=duration)
        print(label, "\t", len(obsList), "\t", durationDelta, end="\t")
        return result

    @staticmethod
    def stringifyDiscrete(obsList, label):
        result = "\t{\n\t\tlabel:\"" + label + "\",\n"
        result += "\t\tUIcomponent:\"" + label + "\",\n"
        result += "\t\ttimes: [\n"
        for obs in obsList:
            result += "\t\t\t{\"starting_time\": " + str(Game.transformObs(obs)) + ", \"display\":\"circle\"},\n"
        result += "\t\t]\n\t},"
        print(label, "\t", len(obsList), end="\t")
        return result

    def __str__(self):
        result = "\nvar data" + self.varName + " = [\n"
        result += Game.stringifyDuration([], self.varName) # Dummy row for the PID
        print("Game Duration\t", self.duration, end="\t")
        result += Game.stringifyDuration(self.slider, "Rewind Slider")
        result += Game.stringifyDuration(self.boardHighlights, "Board Highlights")
        result += Game.stringifyDuration(self.explHighlights, "Expl. Highlights")
        result += Game.stringifyDuration(self.STTexpl, "StTime showing")
        result += Game.stringifyDuration(self.SMexpl, "SMult showing")
        result += Game.stringifyDuration(self.BTWexpl, "BtoW showing")
        result += Game.stringifyDiscrete(self.tabChanges, "Change xAgent")
        result += Game.stringifyDiscrete(self.steps, "Step")
        result += "\n];\n"
        print()
        return result

class Session(Game):
    def __init__(self, filename, explanationMode):
        super().__init__(filename, explanationMode, 1)
        self.gameCreations = []

    def __str__(self):
        result = "\nvar data" + self.varName + " = [\n"
        result += Session.stringifyDuration([], "_____________" + self.varName)  # Dummy row for the PID
        print("Session Duration\t", self.duration, end="\t")
        result += Session.stringifyDuration(self.slider, "Rewind Slider")
        result += Session.stringifyDuration(self.boardHighlights, "Board Highlights")
        result += Session.stringifyDuration(self.explHighlights, "Expl. Highlights")
        result += Session.stringifyDuration(self.STTexpl, "StTime showing")
        result += Session.stringifyDuration(self.SMexpl, "SMult showing")
        result += Session.stringifyDuration(self.BTWexpl, "BtoW showing")
        result += Session.stringifyDiscrete(self.tabChanges, "Change xAgent")
        result += Session.stringifyDiscrete(self.gameCreations, "New Game")
        result += Session.stringifyDiscrete(self.steps, "Step")
        result += "\n];\n"
        print()
        return result
