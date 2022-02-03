import torch

from agent.CnnAgent import CnnAgent
from random import randint, seed
from game.Square import Square
from game.Board import Board

m = 9
n = 4
k = 4
numOutcomes = 3

seed(45134)
traingLoopIters = 1000
numPrints = 40
batchSize = 32 #FIXME Pick a batch size, something like 32-256, could be as low as 8
printPeriod = traingLoopIters / numPrints
maxBoardStates = 3 ** (m * n)
typeInThisGame = Square.X_HAS

# FIXME to HPC, upload code to server, e.g. on home directory, run with python, setting up pytorch on the server is a little weird
# point to CUDA correctly:
#   export PATH=/usr/local/eecsapps/cuda/cuda-10.0/bin/${PATH:+:${PATH}}
#   export LD_LIBRARY_PATH=/usr/local/eecsapps/cuda/cuda-10.0/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}

logger = None

toTrain = CnnAgent("wave2")#, "r5l4midTraining125000.pth")
toTrain.isLearning = True
toTrain.gamesExperienced = toTrain.gamesAtWhichTrainingConcludes = traingLoopIters # set these the same so its appropriately LOW temp softmax
print("Max board states: ", maxBoardStates)
print("training", toTrain.privateName, " for ", traingLoopIters,  " loop iterations, with batch size ", batchSize, ", playing ", typeInThisGame)

# a good test board ID: 124477666002372083
for i in range(int(traingLoopIters)):
    testBoardList = []
    while len(testBoardList) < batchSize:
        randomNum = randint(0, maxBoardStates)
        board, boardIsUseful = Board.createBoardFromNumber(m, n, k, randomNum)
        if boardIsUseful:
            testBoardList.append(board)

    # FIXME check cat, might need to set a param on which dim to stack (first dim should be >1)
    # FIXME do the same thing for target. Weight update should nt need to change, UNTIL we rewrite loss
    nnOutput = torch.cat([toTrain.nn.evaluateBoard(testBoard, typeInThisGame) for testBoard in testBoardList], dim=0)
    #nnOutput = toTrain.nn.evaluateBoard(testBoard, typeInThisGame)
    target = torch.cat([toTrain.computeTargetTensor(nnOutput, testBoard, typeInThisGame) for testBoard in testBoardList], dim=0)
    #target = toTrain.computeTargetTensor(nnOutput, testBoard, typeInThisGame)

    loss = toTrain.nn.weightUpdate(nnOutput, target, toTrain.optimizer)

    #print("from Uniform random sampling", altTarget.reshape((numOutcomes, n, m)).transpose(0, 2))
    #print("from MCTS", target.reshape((numOutcomes, n,m)).transpose(0, 2))
    print(i+1, "\t/\t", traingLoopIters, "\tLoss:\t" + str(loss.item()), target.shape)

    if (i + 1) % printPeriod == 0:
        toTrain.save("midTraining" + str(i + 1) + ".pth")

print("\ntraining complete")
