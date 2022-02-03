from OpenGL.GL import *
import torch

import UI.UtilsUI as utils
from game.Square import Square

# This class stores the board and which pieces are on it
class Board:
    def __init__(self, m, n):
        self.m = m # M is intended to be the X variable (col)
        self.n = n # N is intended to be the Y variable (row)
        self.clearBoard()

    # remove all the pieces from the board, and clear the highlights
    def clearBoard(self):
        # this is now to be indexed [m][n]. Python doesnt really do 2d arrays, but nested lists are close enough.
        self.theBoard = [[Square(Square.OPEN) for _ in range(self.n)] for _ in range(self.m)]
        self.highlighted = []
        self.winHighlight = []
        self.pendingMove = []

    # convert a move from indexing the board [1..col*row] to an index pair [1..col][1..row]
    def convertActionVecToIdxPair(self, actionLongVec):
        numCols = self.m
        row = int(actionLongVec / numCols)
        col = int(actionLongVec % numCols)
        return col, row

    # helpers that determine if a move is on the board or legal, under both indexing schema
    def moveIsOnBoard(self, mIndex, nIndex):
        return 0 <= mIndex < self.m and 0 <= nIndex < self.n
    def moveIsLegal(self, mIndex, nIndex):
        return self.theBoard[mIndex][nIndex] == Square.OPEN
    def longMoveIsLegal(self, longIndex):
        col, row = self.convertActionVecToIdxPair(longIndex)
        return self.theBoard[col][row] == Square.OPEN

    # This function attempts to add a piece to the board, and returns whether the move was legal
    def addPiece(self, mIndex, nIndex, pieceType):
        move = (mIndex, nIndex)
        if self.theBoard[mIndex][nIndex] == Square.OPEN:
            self.theBoard[mIndex][nIndex] = pieceType
            return True
        else:
            return False

    # setter and getter for a square on the board
    def getPiece(self, mIndex, nIndex):
        return self.theBoard[mIndex][nIndex]
    def setPiece(self, mIndex, nIndex, pieceType):
        self.theBoard[mIndex][nIndex] = pieceType

    # returns whether or not any moves remain
    def numPiecesEachKind(self):
        numXs = 0
        numOs = 0
        for j in range(self.n):
            for i in range(self.m):
                if Square.X_HAS == self.theBoard[i][j]:
                    numXs += 1
                elif Square.O_HAS == self.theBoard[i][j]:
                    numOs += 1
        return numXs, numOs

    # returns whether or not any moves remain
    def movesRemain(self):
        for j in range(self.n):
            for i in range(self.m):
                if Square.OPEN == self.theBoard[i][j]:
                    return True
        return False


    # returns whether or not any moves remain
    def movesRemain(self):
        for j in range(self.n):
            for i in range(self.m):
                if Square.OPEN == self.theBoard[i][j]:
                    return True
        return False

    # returns a list containing index pairs for each empty square on the board
    def getOpenSquares(self):
        openSquares = []
        for j in range(self.n):
            for i in range(self.m):
                if Square.OPEN == self.theBoard[i][j]:
                    openSquares.append((i,j))
        return openSquares

    # returns whether or not a player has a sequence of the specified length on the board
    def hasPlayerWon(self, sequenceLength, player):
        # Scan m dimension
        for i in range(self.m-sequenceLength+1):
            for j in range(self.n):
                for k in range(sequenceLength):
                    if self.theBoard[i+k][j] != player:
                        break
                    elif k == sequenceLength - 1:
                        for winFlagStep in range(sequenceLength):
                            self.winHighlight.append((i+winFlagStep, j))
                        return True

        # Scan n dimension
        for i in range(self.m):
            for j in range(self.n-sequenceLength+1):
                for k in range(sequenceLength):
                    if self.theBoard[i][j+k] != player :
                        break
                    elif k == sequenceLength - 1:
                        for winFlagStep in range(sequenceLength):
                            self.winHighlight.append((i, j+winFlagStep))
                        return True

        # Scan diagonal from upper left to lower right
        for i in range(self.m-sequenceLength+1):
            for j in range(self.n-sequenceLength+1):
                for k in range(sequenceLength):
                    if self.theBoard[i+k][j+k] != player:
                        break
                    elif k == sequenceLength - 1:
                        for winFlagStep in range(sequenceLength):
                            self.winHighlight.append((i+winFlagStep, j+winFlagStep))
                        return True

        # Scan diagonal from lower left to upper right
        for i in range(sequenceLength-1, self.m):
            for j in range(self.n-sequenceLength+1):
                for k in range(sequenceLength):
                    if self.theBoard[i-k][j+k] != player:
                        break
                    elif k == sequenceLength - 1:
                        for winFlagStep in range(sequenceLength):
                            self.winHighlight.append((i-winFlagStep, j+winFlagStep))
                        return True

        # if we got here, no one has won yet
        return False

    def getBoardID(self):
        seedNum = 0
        for j in range(self.n):
            for i in range(self.m):
                expHere = j*self.m+i
                if self.theBoard[i][j] == Square.X_HAS:
                    seedNum += 1 * 3**expHere
                elif self.theBoard[i][j] == Square.O_HAS:
                    seedNum += 2 * 3**expHere

        return seedNum

    @staticmethod
    def createBoardFromNumber(m, n, k, seedNum):
        result = Board(m, n)

        # actually fill in the board
        for j in range(n):
            for i in range(m):
                if seedNum == 0:
                    break
                remainder = seedNum % 3
                seedNum = seedNum // 3
                if remainder == 1:
                    result.theBoard[i][j] = Square.X_HAS
                elif remainder == 2:
                    result.theBoard[i][j] = Square.O_HAS

            if seedNum == 0: # booooo, where is my goto :(  BTW, this is the only time its ok to use a goto, breaking out of nested loop in same fn
                break

        # check to see if this board is good for training, if not, say so when returning it
        boardIsUseful = True
        numXs, numOs = result.numPiecesEachKind()
        if abs(numXs - numOs) > 1:
            boardIsUseful = False
        elif result.hasPlayerWon(k, Square.X_HAS):
            boardIsUseful = False
        elif result.hasPlayerWon(k, Square.O_HAS):
            boardIsUseful = False
        return result, boardIsUseful

    def exportToNN(self, myType, verbose=False):
        channels = 2
        batchSize = 1
        boardTensor = torch.zeros(batchSize, channels, self.n, self.m)

        if myType == Square.X_HAS:
            oppType = Square.O_HAS
        else:
            oppType = Square.X_HAS


        #FIXME investigate a fancy numpy 1 liner, by finding a "mask" "where index"
        # doctor up the tensor with current board state
        for j in range(self.n):
            for i in range(self.m):
                # switching indexing here because the torch doesnt use the same nested array layout as built-in data types
                if self.theBoard[i][j] == myType:
                    boardTensor[0][0][j][i] = 1
                elif self.theBoard[i][j] == oppType:
                    boardTensor[0][1][j][i] = 1

        #textToLog += str(self)
        #textToLog += "\nboardTensor in board::export\n" + str(boardTensor)

        return boardTensor

    # This function handles printing boards
    def __repr__(self):
        result = "\n"
        for j in range(self.n):
            for i in range(self.m):
                result += str(self.theBoard[i][j])
            result += "\n"

        return result

    def render(self, boardDispListIdx, circleDispListIdx, exDispListIdx, boxDispListIdx, squareSize, xColor, oColor, history, font, numMovesToFilter):
        glPushMatrix()
        offset = .0375
        glTranslatef(offset, offset, 0)
        glScalef(.9525, .9525, 1)  # shrink a bit so we have a border
        # draw the X's
        glLineWidth(7)
        glColor3ubv(xColor[:-1])
        numTotalMoves = len(history)
        for j in range(self.n):
            for i in range(self.m):
                if Square.X_HAS == self.theBoard[i][j]:
                    try:
                        moveNumber = history.index((i, j))
                    except ValueError:
                        moveNumber = -1
                    if moveNumber < numTotalMoves - numMovesToFilter:
                        self.theBoard[i][j].emitGeometry(i, j, squareSize, exDispListIdx, moveNumber, font)

        # draw the O's
        glColor3ubv(oColor[:-1])
        for j in range(self.n):
            for i in range(self.m):
                if Square.O_HAS == self.theBoard[i][j]:
                    try:
                        moveNumber = history.index((i, j))
                    except ValueError:
                        moveNumber = -1
                    if moveNumber < numTotalMoves - numMovesToFilter:
                        self.theBoard[i][j].emitGeometry(i, j, squareSize, circleDispListIdx, moveNumber, font)

        # draw the WIN highlighted squares (before UI highlighting)
        highlightColor = utils.yellowWong
        for idxList in self.winHighlight:
            square = self.theBoard[idxList[0]][idxList[1]]
            if idxList in history:
                moveNumber = history.index(idxList)
            else:
                moveNumber = -1
            if moveNumber < numTotalMoves - numMovesToFilter:
                square.emitHighlight(idxList[0], idxList[1], squareSize, xColor, oColor, highlightColor, circleDispListIdx, exDispListIdx, boxDispListIdx, moveNumber, font)

        # Now we can draw UI highlighting, so it sits atop the win highlight (same code but all highlights use same color)
        for idxList in self.highlighted:
            square = self.theBoard[idxList[0]][idxList[1]]
            if idxList in history:
                moveNumber = history.index(idxList)
            else:
                moveNumber = -1
            square.emitHighlight(idxList[0], idxList[1], squareSize, highlightColor, highlightColor, highlightColor, circleDispListIdx, exDispListIdx, boxDispListIdx, moveNumber, font)


        # draw the pending moves
        allHighlights = self.pendingMove
        highlightColor = utils.black
        for idxList in allHighlights:
            square = self.theBoard[idxList[0]][idxList[1]]
            moveNumber = -1
            square.emitHighlight(idxList[0], idxList[1], squareSize, xColor, oColor, highlightColor, circleDispListIdx,
                                 exDispListIdx, boxDispListIdx, moveNumber, font)

        # draw the grid lines
        glLineWidth(2)
        glColor4ubv(utils.black)
        glCallList(boardDispListIdx)
        glPopMatrix()
