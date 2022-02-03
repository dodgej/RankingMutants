from copy import deepcopy
from functools import reduce, partial
from random import randint

import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical

from game.MNKGame import MNKGame
from agent.AgentBase import AgentBase
from agent.UtilsAgent import ScalarField
from agent.CNNforMNK import CNNforMNK
from agent.RandomAgent import RandomAgent
from agent.ExplainerForCNN import ExplainerForCNN
from game.Board import Board
from game.Square import Square

from settings import settings

# This agent uses a convolutional neural network to compute predicted outcomes for each move.
# Then, the outcomes are scored to select moves
class CnnAgent(AgentBase):
    def __init__(self, agentName, filename=None):
        AgentBase.__init__(self, agentName)
        self.nn = CNNforMNK(settings.m, settings.n, settings.numOutcomes)

        if torch.cuda.is_available():
            self.nn = self.nn.cuda()

        self.explainer = ExplainerForCNN()

        self.movesMade = 0
        self.gamesExperienced = 0
        self.isConstraintSatGuaranteed = True

        self.perceptionPoisoningFn = None #FIXME not sure this is how I want to init this
        self.actuatorPoisoningFn = None

        self.peakLR = 1
        self.minConcentration = .2
        self.gamesAtWhichTrainingConcludes = 100
        self.numGamesToEstimateValue = 3600

        # network reward function parameters
        self.rewardGameWin = 1.0
        self.rewardGameDraw = 0.0
        self.penaltyGameLoss = -1.0

        # optimizer needs to live in the AGENT, not the Module
        regularization = 1e-5
        learningRate = 1e-3
        self.optimizer = optim.Adam(self.nn.parameters(), lr=learningRate, weight_decay=regularization)

        if filename:
            self.load("../agents/" + filename)

    # each time a new game is created we need to do a little bit of bookkeeping
    def onNewGame(self):
        self.explainer.clearData()
    def onGameOver(self):
        if self.isLearning:
            self.gamesExperienced += 1

    # loads neural network weights from a file
    def load(self, path):
        self.nn.load_state_dict(torch.load(path))

        # Allow the network to continue to learn after loading (Some possible control flow improvements could be made here)
        for _, param in self.nn.named_parameters():
            param.requires_grad = True
        return True

    # dumps neural network weights to a file
    def save(self, path):
        torch.save(self.nn.state_dict(), path)
        return True

    # this function takes a NN output, scores it, and dumps output for explanations
    def computeScores(self, outcomeTensor, packingFn):
        # unpack the tensor into these matrices so that we can compute scores and create visualization elements more easily
        winPercent = torch.zeros(settings.n, settings.m)
        drawPercent = torch.zeros(settings.n, settings.m)
        lossPercent = torch.zeros(settings.n, settings.m)

        # do the unpacking here
        for j in range(settings.n):
            for i in range(settings.m):
                # Note: weird indexing because torch aligns matrices differently from built in data types
                winPercent[j][i] = outcomeTensor[0][j][i]
                lossPercent[j][i] = outcomeTensor[1][j][i]
                drawPercent[j][i] = outcomeTensor[2][j][i]
        result = winPercent*self.rewardGameWin + lossPercent*self.penaltyGameLoss + drawPercent*self.rewardGameDraw

        # now we can stock up our visualization fields
        fields = [ScalarField(result), ScalarField(winPercent), ScalarField(lossPercent), ScalarField(drawPercent)]
        packingFn(fields)
        return result

    # this temperature is used to do the explore/exploit tradeoff in the gumbel softmax
    def computeTemperature(self):
        maxTemp = 20
        minTemp = .1

        if not self.isLearning:
            return minTemp

        range = maxTemp - minTemp
        alpha = self.gamesExperienced / self.gamesAtWhichTrainingConcludes

        return (1-alpha)*range+minTemp

    # select a move by doing a forward pass on the NN, scoring the outcomes, Gumbel softmaxing to get a probability distribution,
    # then enforcing domain constraints before finally sampling.
    def move(self, board, typeInThisGame, logger):
        textToLog = "-----------------------------------\n"
        textToLog += "Player " + self.privateName + " preparing to make a move, playing " + str(typeInThisGame)
        textToLog += " on this board\n" + str(board)

        nnOutput = self.nn.evaluateBoard(board, typeInThisGame)
        outcomeTensor = torch.reshape(nnOutput, (settings.numOutcomes, settings.n, settings.m))

        # convert NN outputs to scores for each move
        scoreMatrix = self.computeScores(outcomeTensor, self.explainer.unpackToPredictions)
        textToLog += "\nNN outcome tensor (transposed to align with the sampled tensor)\n" + str(outcomeTensor.transpose(0, 2))
        textToLog += "\nScore Matrix\n" + str(scoreMatrix)

        # domain constraint enforcement step, set outputs
        if self.isConstraintSatGuaranteed:
            for j in range(settings.n):
                for i in range(settings.m):
                    if not board.moveIsLegal(i, j):
                        scoreMatrix[j][i] = -1

            textToLog += "\nPost-CONSTRAINT Score Matrix\n" + str(scoreMatrix)

        # scaling by 100 so the softmax is more well behaved (it doesnt like -1,1 land much)
        scoreLongVector = scoreMatrix.reshape(settings.n * settings.m) * 100

        temperature = self.computeTemperature()
        actionProbs = nn.functional.gumbel_softmax(scoreLongVector, temperature)

        # grab qValues for explanation reasons
        if typeInThisGame == Square.X_HAS:
            self.explainer.captureQValues(scoreLongVector.tolist(), board)
        textToLog += "\nTemperature: " + str(temperature)
        textToLog += "\nActionProbs\n" + str(actionProbs.view(settings.n, settings.m))

        try:
            # select an action by sampling the posterior (this will add some randomness, but not a true explore/exploit tradeoff)
            categorical = Categorical(actionProbs.view(-1, settings.m*settings.n))
        except:
            print(self.privateName, temperature, board, scoreLongVector, actionProbs)
        moveX, moveY = board.convertActionVecToIdxPair(categorical.sample())

        textToLog += "\nMove: " + str(moveX) + " " + str(moveY)

        if self.isLearning:
            self.movesMade += 1
            target = self.computeTargetTensor(nnOutput, board, typeInThisGame)
            loss = self.nn.weightUpdate(nnOutput, target, self.optimizer)

            textToLog += "TARGET outcome tensor (from sampling " + str(self.numGamesToEstimateValue) + " games per move): \n" + str(target.transpose(0, 2))
            textToLog += "\nOUTPUT outcome tensor (from NN):\n" + str(nnOutput.reshape((settings.numOutcomes, settings.n, settings.m)).transpose(0, 2))
            textToLog += "\nLoss: " + str(loss.item()) + " at game count " + str(self.gamesExperienced) + " out of " + str(self.gamesAtWhichTrainingConcludes)

        if logger:
            logger.DoLogText(textToLog)

        return moveX, moveY

    def computeTargetTensor(self, nnOutput, board, typeInThisGame):
        #targetTensor = self.computeTargetTensorPMCGS(nnOutput, board, typeInThisGame)
        targetTensor = self.computeTargetTensorMCTS(nnOutput, board, typeInThisGame)

        return torch.reshape(targetTensor, (1, settings.numOutcomes * settings.n * settings.m))

    # this function is used to get the "ground truth" that the NN should have output, generated by sampling outcomes, usig uniform random sampling
    def computeTargetTensorPMCGS(self, nnOutput, board, typeInThisGame):
        '''
        controlPanel = settings.controlPanel
        # create agents to play as surrogates if we are doing RANDOM rollouts
        if controlPanel.randomRolloutButton.GetValue():
            myAgent = RandomAgent("myRando")
            opponent = RandomAgent("oppRando")
        else: # or if we are doing POLICY rollouts, just shallow copy some stuff
            myAgent = self
            if game.xPlayer == self:
                opponent = game.oPlayer
            else:
                opponent = game.xPlayer
        '''
        myAgent = RandomAgent("myRando")
        opponent = RandomAgent("oppRando")

        # turn off learning so our simulated games dont trigger weight updates and infinitely recurse
        oldLearningSettingSelf = self.isLearning
        oldLearningSettingOpp = opponent.isLearning
        self.isLearning = False
        opponent.isLearning = False

        targetTensor = torch.zeros(settings.numOutcomes, settings.n, settings.m)
        # again note the weird indexing in here cuz torch aligns matrices differently from built-in
        for j in range(settings.n):
            for i in range(settings.m):
                if not board.moveIsLegal(i,j): # no need to sample for illegal moves
                    targetTensor[0][j][i] = 0 # wins
                    targetTensor[1][j][i] = 1 # losses
                    targetTensor[2][j][i] = 0 # draws
                else:
                    #FIXME to make fair against MCTS, we need to divide
                    gamesToPlayHere = int(self.numGamesToEstimateValue/(settings.m*settings.n))
                    inverseNumGamesToEstimateValue = 1.0 / gamesToPlayHere
                    for _ in range(gamesToPlayHere):
                        # copy the "current" board and make the move we are considering
                        if typeInThisGame == Square.X_HAS:
                            testGame = MNKGame(deepcopy(board), myAgent, opponent, True, False) # do not log these subgames
                        else:
                            testGame = MNKGame(deepcopy(board), opponent, myAgent, False, False)  # do not log these subgames
                        gameOver, winner = testGame.advanceSimulatorWithMove(i,j)

                        # play a random game from here (if the test move didnt end the game)
                        if not gameOver:
                            winner, _ = testGame.playGame()  # no logging here, (too much output)

                        # do bookkeeping based on who won by accumulating a sum
                        if winner == myAgent:
                            targetTensor[0][j][i] += 1.0
                        elif winner == opponent:
                            targetTensor[1][j][i] += 1.0
                        else:
                            targetTensor[2][j][i] += 1.0
                    # Normalize to a win%
                    targetTensor[0][j][i] *= inverseNumGamesToEstimateValue # wins
                    targetTensor[1][j][i] *= inverseNumGamesToEstimateValue # losses
                    targetTensor[2][j][i] *= inverseNumGamesToEstimateValue # draws

        # simulation over, return learning setting to old value
        self.isLearning = oldLearningSettingSelf
        opponent.isLearning = oldLearningSettingOpp

        # this call isnt needed other than for vis purposes
        self.computeScores(targetTensor, self.explainer.unpackToSampled)

        # will need this tensor over on the GPU if we are using GPUs, in order to do the backward pass
        if torch.cuda.is_available():
            targetTensor = targetTensor.cuda()
        return torch.reshape(targetTensor, (1, settings.numOutcomes*settings.n*settings.m))

    # This function runs a training loop between THIS agent and the specified opponent on the specified board
    def trainAgainstOLD(self, opponent, board, games, peakLR, logging):
        self.isLearning = True
        self.gamesExperienced = 0
        self.gamesAtWhichTrainingConcludes = games
        self.peakLR = peakLR

        print("training", self.privateName, " against ", opponent.privateName, " for ", self.gamesAtWhichTrainingConcludes, " games.")
        print("Games\tRecord\tAverageMoveCount")

        numPrints = 40
        printPeriod = games / numPrints
        totalRecord = [0,0,0]
        totalMoveCount = 0
        for i in range(int(games)):
            theGame = MNKGame(deepcopy(board), self, opponent, i % 2 == 0, logging)
            winner, moveCount = theGame.playGame()

            totalMoveCount += moveCount
            if winner == self:
                totalRecord[0] += 1
            elif winner == None:
                totalRecord[2] += 1
            else:
                totalRecord[1] += 1

            if (i + 1) % printPeriod == 0:
                self.save("midTraining" + str(i+1) + ".pth")
                print(self.gamesExperienced, "\t", totalRecord, "\t", totalMoveCount / printPeriod)
                totalRecord = [0, 0, 0]
                totalMoveCount = 0

        print("\ntraining complete")

    # This function runs a training loop between THIS agent and the specified opponent on the specified board
    def trainAgainst(self, opponent, board, games, logging):
        self.isLearning = True
        self.gamesExperienced = games #FIXME reframe this as MOVES
        self.gamesAtWhichTrainingConcludes = games
        print("training", self.privateName, " against ", opponent.privateName, " for ",
              self.gamesAtWhichTrainingConcludes, " games.")

        numPrints = 40
        printPeriod = games / numPrints

        maxBoardStates = 3 ** (settings.m * settings.n)
        boardIsUseful = False
        for i in range(int(games)):
            while not boardIsUseful:
                testBoard, boardIsUseful = Board.createBoardFromNumber(settings.m, settings.n, settings.k, randint(0, maxBoardStates))

            game = MNKGame(testBoard, self, opponent, i % 2 == 0, logging)
            typeInThisGame = game.getType(self)

            #FIXME how to batchify this?
            nnOutput = self.nn.evaluateBoard(testBoard, typeInThisGame)
            target = self.computeTargetTensor(nnOutput, testBoard, typeInThisGame)
            loss = self.nn.weightUpdate(nnOutput, target, self.optimizer)

            print(i, "/", games, " Loss:\t" + str(loss.item()))

            if (i + 1) % printPeriod == 0:
                self.save("midTraining" + str(i + 1) + ".pth")

        print("\ntraining complete")

    def noisifySelf(self, noiseSDs):
        originalWeights = deepcopy(self.nn)
        mean = 0
        for sd in noiseSDs:
            self.nn = deepcopy(originalWeights)
            self.nn.noisifyLayer(self.nn.conv1, mean, sd)
            self.save("../agents/noisifiedConv1SD"+str(sd)+".pth")
        for sd in noiseSDs:
            self.nn = deepcopy(originalWeights)
            self.nn.noisifyLayer(self.nn.conv2, mean, sd)
            self.save("../agents/noisifiedConv2SD"+str(sd)+".pth")
        for sd in noiseSDs:
            self.nn = deepcopy(originalWeights)
            self.nn.noisifyLayer(self.nn.conv3, mean, sd)
            self.save("../agents/noisifiedConv3SD"+str(sd)+".pth")
        for sd in noiseSDs:
            self.nn = deepcopy(originalWeights)
            self.nn.noisifyLayer(self.nn.conv4, mean, sd)
            self.save("../agents/noisifiedConv4SD"+str(sd)+".pth")
        for sd in noiseSDs:
            self.nn = deepcopy(originalWeights)
            self.nn.noisifyLayer(self.nn.conv5, mean, sd)
            self.save("../agents/noisifiedConv5SD"+str(sd)+".pth")
        for sd in noiseSDs:
            self.nn = deepcopy(originalWeights)
            self.nn.noisifyLayer(self.nn.fc1, mean, sd)
            self.save("../agents/noisifiedFc1SD"+str(sd)+".pth")



    # this function just dumps out losses as the LR changes, to tune that parameter
    def reportOptimalLRRange(self, game):
        startingLR = .000001
        LRtoTest = startingLR
        board = game.board

        typeInThisGame = game.getType(self)
        nnOutput = self.nn.evaluateBoard(board, game.getType(self))
        target = self.computeTargetTensor(nnOutput, board, typeInThisGame)
        self.optimizer.lr = LRtoTest
        loss = self.nn.weightUpdate(nnOutput, target, self.optimizer)
        print("learning Rate\tLoss\n")
        print(LRtoTest, "\t", loss.item())

        for i in range(100):
            LRtoTest *= 1.2
            nnOutput = self.nn.evaluateBoard(board, game.getType(self))
            self.optimizer.lr = LRtoTest
            loss = self.nn.weightUpdate(nnOutput, target, self.optimizer)
            print(LRtoTest, "\t", loss.item())

    def render(self, game, squareSize, font, numMovesToFilter):
        self.explainer.render(game, squareSize, self.rewardGameDraw, self.penaltyGameLoss, font, numMovesToFilter)