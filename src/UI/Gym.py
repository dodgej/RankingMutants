from copy import deepcopy
from functools import reduce, partial
from random import randint, shuffle

from agent.CnnAgent import CnnAgent
from agent.HumanAgent import HumanAgent
from agent.RandomAgent import RandomAgent
from game.Board import Board
from game.MNKGame import MNKGame
from game.Square import Square

from settings import settings


class Gym:
    def __init__(self, logger):

        self.agents = []
        self.boards = []
        self.agentsToAssess = []
        self.agentsToTrainWith = []

        self.perfLog = logger
        self.perfLog.DoLogText("Start of performance log\n")

        self.benchmark = self.createBenchmarkAgents()

        ''''''
        # set up the training target
        old = CnnAgent("1-Base", "r5l4midTraining125000.pth")
        self.agentsToAssess.append(old)



        dummy1 = CnnAgent("Training Dummy 1") # FIXME pick some weights for this one
        self.agentsToTrainWith.append(dummy1)

        dummy2 = CnnAgent("Training Dummy 2", "r5l4midTraining125000.pth") # FIXME pick some weights for this one
        self.agentsToTrainWith.append(dummy2)

        dummy3 = CnnAgent("Training Dummy 3")  # FIXME pick some weights for this one
        self.agentsToTrainWith.append(dummy3)

        dummy4 = CnnAgent("Training Dummy 4")  # FIXME pick some weights for this one
        self.agentsToTrainWith.append(dummy4)

        dummy5 = CnnAgent("Training Dummy 5")  # FIXME pick some weights for this one
        self.agentsToTrainWith.append(dummy5)

        dummy6 = CnnAgent("Training Dummy 6")  # FIXME pick some weights for this one
        self.agentsToTrainWith.append(dummy6)

        #sampledAgents = self.createSampledAgents()
        #trainedAgents = self.createTrainedAgents()
        #poisonedAgents = self.createPoisonedAgents()
        mutatedAgents = self.createMutatedAgents()

        #self.agentsToAssess += sampledAgents
        #self.agents += trainedAgents
        #self.agents += poisonedAgents
        self.agentsToAssess += mutatedAgents
        #self.agentsToAssess += self.benchmark


        if settings.enableHumanPlay:
            human = HumanAgent("Human")
            self.agentsToTrainWith.append(human)
        if settings.enableDevControls:
            self.agents = self.agentsToAssess
            list.sort(self.agents, key=lambda agent: agent.privateName)
        else:
            self.agents = self.agentsToTrainWith
            shuffle(self.agentsToAssess)

        '''

        #FIXME test board creation here:
        maxBoardStates = 3**(settings.m*settings.n)
        testInputID = randint(0, maxBoardStates)
        testBoard, boardIsUseful = Board.createBoardFromNumber(settings.m, settings.n, settings.k, testInputID)
        testOutputID = testBoard.getBoardID()
        print("input ", testInputID, " output ", testOutputID)

        usefulCount = 0
        uselessCount = 0
        for _ in range(50000):
            testBoard, boardIsUseful = Board.createBoardFromNumber(settings.m, settings.n, settings.k, randint(0, maxBoardStates))
            if boardIsUseful:
                usefulCount += 1
            else:
                uselessCount += 1

        print("Encountered ", usefulCount, " useful boards and ", uselessCount, " useless ones")

        '''

        #for seed in range(maxBoardStates):
        #    testBoard = Board.createBoardFromNumber(settings.m, settings.n, settings.k, seed)

        # set up the pre-built boards
        self.boards.append((Board(settings.m, settings.n), "Empty"))

        winBoard, isUseful = Board.createBoardFromNumber(settings.m, settings.n, settings.k, 21308500879)
        if isUseful: self.boards.append((winBoard, "W Available"))

        forceWinBoard, isUseful = Board.createBoardFromNumber(settings.m, settings.n, settings.k, 15262430256014)
        if isUseful: self.boards.append((forceWinBoard, "Forced W Avail"))

        lossBoard, isUseful = Board.createBoardFromNumber(settings.m, settings.n, settings.k, 16659199131)
        if isUseful: self.boards.append((lossBoard, "Avoid L"))

        forceLossBoard, isUseful = Board.createBoardFromNumber(settings.m, settings.n, settings.k, 50588276480718184)
        if isUseful: self.boards.append((forceLossBoard, "Avoid Forced L"))

    @staticmethod
    def createBenchmarkAgents():
        result = []

        random = RandomAgent("bRANDy")
        result.append(random)
        return result

    @staticmethod
    def createSampledAgents():
        result = []

        for i in range(25, 450, 25):
            name = "sample" + str(i)
            fileName = "midTraining" + str(i) + ".pth"
            sampleHere = CnnAgent(name, fileName)
            result.append(sampleHere)

        return result

    @staticmethod
    def createMutatedAgents():
        result = []

        conv1SDp01 = CnnAgent(  "conv1SDp01", filename="noisifiedConv1SD0.01.pth")
        conv1SDp1 = CnnAgent(   "conv1SDp1", filename="noisifiedConv1SD0.1.pth")
        conv1SD1 = CnnAgent(    "6-MedNoiseLayer1", filename="noisifiedConv1SD1.pth")
        conv1SD10 = CnnAgent(   "conv1SD10", filename="noisifiedConv1SD10.pth")

        conv2SDp01 = CnnAgent(  "conv2SDp01", filename="noisifiedConv2SD0.01.pth")
        conv2SDp1 = CnnAgent(   "2-LowNoiseLayer2", filename="noisifiedConv2SD0.1.pth")
        conv2SD1 = CnnAgent(    "conv2SD1", filename="noisifiedConv2SD1.pth")
        conv2SD10 = CnnAgent(   "conv2SD10", filename="noisifiedConv2SD10.pth")

        conv3SDp01 = CnnAgent(  "conv3SDp01", filename="noisifiedConv3SD0.01.pth")
        conv3SDp1 = CnnAgent(   "3-LowNoiseLayer3", filename="noisifiedConv3SD0.1.pth")
        conv3SD1 = CnnAgent(    "conv3SD1", filename="noisifiedConv3SD1.pth")
        conv3SD10 = CnnAgent(   "conv3SD10", filename="noisifiedConv3SD10.pth")

        conv4SDp01 = CnnAgent(  "conv4SDp01", filename="noisifiedConv4SD0.01.pth")
        conv4SDp1 = CnnAgent(   "conv4SDp1", filename="noisifiedConv4SD0.1.pth")
        conv4SD1 = CnnAgent(    "5-MedNoiseLayer4", filename="noisifiedConv4SD1.pth")
        conv4SD10 = CnnAgent(   "conv4SD10", filename="noisifiedConv4SD10.pth")

        conv5SDp01 = CnnAgent(  "conv5SDp01", filename="noisifiedConv5SD0.01.pth")
        conv5SDp1 = CnnAgent(   "conv5SDp1", filename="noisifiedConv5SD0.1.pth")
        conv5SD1 = CnnAgent(    "4-MedNoiseLayer5", filename="noisifiedConv5SD1.pth")
        conv5SD10 = CnnAgent(   "conv5SD10", filename="noisifiedConv5SD10.pth")

        fc1SDp01 = CnnAgent(  "fc1SDp01", filename="noisifiedFc1SD0.01.pth")
        fc1SDp1 = CnnAgent(   "fc1SDp1", filename="noisifiedFc1SD0.1.pth")
        fc1SD1 = CnnAgent(    "fc1SD1", filename="noisifiedFc1SD1.pth")
        fc1SD10 = CnnAgent(   "fc1SD10", filename="noisifiedFc1SD10.pth")

        #result.append(conv1SDp01)
        #result.append(conv1SDp1)
        result.append(conv1SD1)
        #result.append(conv1SD10)
        #result.append(conv2SDp01)
        result.append(conv2SDp1)
        #result.append(conv2SD1)
        #result.append(conv2SD10)
        #result.append(conv3SDp01)
        result.append(conv3SDp1)
        #result.append(conv3SD1)
        #result.append(conv3SD10)
        #result.append(conv4SDp01)
        #result.append(conv4SDp1)
        result.append(conv4SD1)
        #result.append(conv4SD10)
        #result.append(conv5SDp01)
        #result.append(conv5SDp1)
        result.append(conv5SD1)
        #result.append(conv5SD10)
        #result.append(fc1SDp01)
        #result.append(fc1SDp1)
        #result.append(fc1SD1)
        #result.append(fc1SD10)
        return result

    # get the names of all the pre-built boards, to populate the drop-down
    def getBoardNames(self):
        boardNames = []
        for board in self.boards:
            boardNames.append(board[1])
        return boardNames

    # get the names of all the agents, but without humans (for populating certain interface elements and ranking battles)
    def getAgentsWithoutHumans(self):
        toReturn = []
        for agent in self.agents:
            if isinstance(agent, HumanAgent):
                continue
            else:
                toReturn.append(agent)
        return toReturn

    # get an agent by name, allowing connecting of UI selections to an agent
    def getAgentWithName(self, inputName):
        for agent in self.agents:
            if inputName == agent.publicName:
                return agent
        print("ERROR - NO AGENT NAMED ", inputName)
        for agent in self.agents:
            print(agent.publicName)
        textToLog = "ERROR - NO AGENT NAMED " + inputName
        settings.frame.usageLog.DoLogText(textToLog)
        return None

    # Read the current UI state to spawn a game between currently selected players
    def createGame(self):
        selection = settings.controlPanel.initialBoardComboBox.GetCurrentSelection()
        theBoard = deepcopy(self.boards[selection][0])

        # get the 2 agent names and setup the agents
        homeAgentName = settings.controlPanel.homeLabel.GetLabel()
        awayAgentName = settings.controlPanel.awayComboBox.GetStringSelection()
        xPlayer = self.getAgentWithName(homeAgentName)
        oPlayer = self.getAgentWithName(awayAgentName)
        xPlayer.type = Square.X_HAS
        oPlayer.type = Square.O_HAS

        # translate home/away and the initiative button into 1P/2P, then bind X/O types
        homeGoesFirst = settings.controlPanel.initiativeButton.Value

        textToLog = "Creating game with" + homeAgentName + " playing " + str(Square.X_HAS) + " against " + awayAgentName
        settings.frame.usageLog.DoLogText(textToLog, addTimestamp=True)

        logging = settings.controlPanel.logAllButton.GetValue()
        return MNKGame(theBoard, xPlayer, oPlayer, homeGoesFirst, logging)

    # spins up a headless training process between the home agent and currently selected opponent, with currently selected hyperparams
    def processTrainHeadless(self, event):
        selection = settings.controlPanel.initialBoardComboBox.GetCurrentSelection()
        theBoard = self.boards[selection][0]
        games = settings.controlPanel.numGamesToTrainSpin.GetValue()

        # get the 2 agent names and convert to the agents themselves
        homeName = settings.controlPanel.homeLabel.GetLabel()
        awayName = settings.controlPanel.awayComboBox.GetStringSelection()
        homeAgent = self.getAgentWithName(homeName)
        awayAgent = self.getAgentWithName(awayName)
        homeAgent.type = Square.X_HAS
        awayAgent.type = Square.O_HAS

        textToLog = "Preparing to train " + homeName + " against " + awayName + "..."
        settings.frame.setStatusAndLog(textToLog)
        self.perfLog.DoLogText(textToLog, addTimestamp=True)

        logging = settings.controlPanel.logAllButton.GetValue()
        homeAgent.trainAgainst(awayAgent, theBoard, games, logging)

        textToLog = "Training complete!!!"
        self.perfLog.DoLogText(textToLog, addTimestamp=True)
        settings.frame.setStatusAndLog(textToLog)

    def processNoisifyButton(self, event):
        homeName = settings.controlPanel.homeLabel.GetLabel()
        homeAgent = self.getAgentWithName(homeName)
        noiseSDs = [.01, .1, 1, 10]
        try:
            homeAgent.noisifySelf(noiseSDs)
            print("Agent noisified!")
        except:
            print("Currently selected agent cannot be noisified!")

            #FIXME set this as status

    # helper for ranking battle, does the head to head matchup alternating playing first and returns the record
    def getRecordFrom1V1(self, challenger, opponent, gamesToTest, logging):
        results1v1 = [0, 0, 0]  # wins losses and draws, between current challenger and current opponent
        for i in range(int(gamesToTest)):
            # play a "home game," where challenger acts first, then swap (hence the /2 in the loop bounds)
            winner, _ = MNKGame(Board(settings.m, settings.n), challenger, opponent, i % 2 == 0, logging).playGame()
            if winner == challenger:
                results1v1[0] += 1
            elif winner == opponent:
                results1v1[1] += 1
            else:
                results1v1[2] += 1
        return results1v1

    # performs a ranking battle between the agents in the gym, generating output along the way, and returning the participants ()
    def rankingBattle(self, gamesToTest):
        agentList = self.getAgentsWithoutHumans()
        logging = settings.controlPanel.logAllButton.GetValue()

        #FIXME remember learning settings and turn them off, then restore state
        for agent in agentList:
            agent.isLearning = False
            agent.isExploring = False

        # create the header row for the log file
        textToLog = "\n%-11s\t" % ""
        for agent in agentList:
            textToLog += "%-11s\t" % agent.privateName
        textToLog += "TOTAL (W, L , D)\n"

        resultsMatrix = []
        for i in range(len(agentList)):
            challenger = agentList[i]
            challenger.type = Square.X_HAS # the challenger will always play X, just to keep things aligned proper-like
            resultsRow = []
            textToLog += "%-11s\t" % challenger.privateName
            for j in range(len(agentList)):
                opponent = agentList[j]
                if j == i:
                    textToLog += "- - - - -\t"
                    resultsRow.append([0,0,0])
                    continue
                elif j < i: # we have this result memoized, but need to flip W-L perspective
                    tempList = deepcopy(resultsMatrix[j][i])
                    swap = tempList[0]
                    tempList[0] = tempList[1]
                    tempList[1] = swap
                    textToLog += str(tempList) + "\t"
                    resultsRow.append(tempList)
                    continue

                opponent.type = Square.O_HAS # and the opponent would correspondingly be O
                results1v1 = self.getRecordFrom1V1(challenger, opponent, gamesToTest, logging)
                textToLog += str(results1v1) + "\t"
                resultsRow.append(results1v1)

            resultsTotal = [0,0,0]
            winList, lossList, drawList = zip(*resultsRow)
            resultsTotal[0] = reduce(lambda a, b: a + b, winList)
            resultsTotal[1] = reduce(lambda a, b: a + b, lossList)
            resultsTotal[2] = reduce(lambda a, b: a + b, drawList)

            textToLog += str(resultsTotal) + "\t" + challenger.publicName + "\n"
            resultsRow.append(resultsTotal)
            resultsMatrix.append(resultsRow)

        textToLog += "\n"

        for i in range(len(agentList)):
            challenger = agentList[i]
            challenger.type = Square.X_HAS # the challenger will always play X, just to keep things aligned proper-like
            resultsTotal = [0, 0, 0]
            for j in range(len(self.benchmark)):
                opponent = self.benchmark[j]
                opponent.type = Square.O_HAS # and the opponent would correspondingly be O
                results1v1 = self.getRecordFrom1V1(challenger, opponent, gamesToTest, logging)
                resultsTotal[0] += results1v1[0]
                resultsTotal[1] += results1v1[1]
                resultsTotal[2] += results1v1[2]
                textToLog += challenger.privateName + " vs " + opponent.privateName + ":\t" + str(results1v1) + "\n"
            textToLog += "Total score for " + challenger.privateName + "\t" + str(resultsTotal) + "("+ challenger.publicName +")\n\n"


        self.perfLog.DoLogText(textToLog)

        # FIXME order the agent list? maybe zip it with results?

        return agentList
