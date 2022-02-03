import UI.UtilsUI as utils
from game.Square import Square

from settings import settings

# This class is essentially in charge of the top level control flow for making a game happen
class MNKGame:
    # set up the place for games to be logged as static data
    gameFilenameStem = "game"
    gameLogPath = "../logs/game/"
    gameNumber = utils.getNextFileNumber(gameLogPath, gameFilenameStem)

    def __init__(self, board, xPlayer, oPlayer, xGoesFirst, logged):
        self.board = board
        self.xPlayer = xPlayer
        self.oPlayer = oPlayer

        self.xPlayer.onNewGame()
        # FIXME I *think* it is the case that we can avoid doing this because this agent does not explain itself on any tab but its own, which is X ONLY
        #self.oPlayer.onNewGame()

        if xGoesFirst:
            self.whoseTurn = self.xPlayer
            self.idleTurn = self.oPlayer
            firstPlayerStr = "X"
        else:
            self.whoseTurn = self.oPlayer
            self.idleTurn = self.xPlayer
            firstPlayerStr = "O"

        self.history = []

        self.logged = logged
        self.gameLog = None
        if logged:
            self.gameLog = utils.LogToFile(MNKGame.gameLogPath, MNKGame.gameFilenameStem, MNKGame.gameNumber, alsoPrint=False)
            textToLog = "Game: " + str(MNKGame.gameNumber) + "\n"
            textToLog += "Initial Board: " + str(board) + "\n"
            textToLog += "X player: " + self.xPlayer.privateName + "\n"
            textToLog += "O player: " + self.oPlayer.privateName + "\n"
            textToLog += "Playing first: " + firstPlayerStr + "\n"
            textToLog += "Winner: ??\n"
            self.gameLog.DoLogText(textToLog)
            self.marker = self.gameLog.logFile.tell()
            MNKGame.gameNumber += 1

    # simple getter method to determine which piece type a player controls in THIS game.
    def getType(self, player):
        if player == self.xPlayer:
            return Square.X_HAS
        elif player == self.oPlayer:
            return Square.O_HAS
        else:
            return None

    def whoWentFirst(self):
        if len(self.history) > 0:
            firstMove = self.history[0]
            if self.board.getPiece(firstMove[0], firstMove[1]) == Square.X_HAS:
                return self.xPlayer
            else:
                return self.oPlayer
        else:
            return self.whoseTurn

    # top level control to play a full game, returning the winner and number of moves in the game.
    def playGame(self):
        winner = None
        for i in range(self.board.m * self.board.n):
            gameOver, winner, moveX, moveY = self.gameStep()
            if gameOver:
                break

        return winner, len(self.history)

    # top level control to advance the gamestate a single step. Returns 4 values: whether the game is over, who won, and the moveX/Y
    def gameStep(self):
        gameOver = False
        winner = None
        moveX = None
        moveY = None

        # first, see if the agent is ready. If not, send it back to the update loop
        if not self.whoseTurn.isReady:
            return gameOver, winner, moveX, moveY

        # second see if we CAN put anymore pieces on the board, if not end the game, else go find a move
        if not self.board.movesRemain():
            gameOver = True
            self.endTheGame(winner)
        else: # request a move from the agent, then try to make it
            typeToMove = self.getType(self.whoseTurn)
            moveX, moveY = self.whoseTurn.move(self.board, typeToMove, self.gameLog)
            gameOver, winner = self.advanceSimulatorWithMove(moveX, moveY)

        return gameOver, winner, moveX, moveY

    # this function helps gameStep by actually MAKING the move
    def advanceSimulatorWithMove(self, moveX, moveY):
        typeInThisGame = self.getType(self.whoseTurn)
        moveWasLegal = self.board.addPiece(moveX, moveY, typeInThisGame)

        # complain if move was not legal (and lose that turn, functionally. This will keep us out of infinite loops where agent keeps trying same illegal things)
        if not moveWasLegal:
            textToLog = "*********ILLEGAL MOVE from " + str(typeInThisGame) + self.whoseTurn.privateName + "(" + self.whoseTurn.publicName + ")" + str((moveX, moveY)) + str(self.board)
            self.gameLog.DoLogText(textToLog)

        # make a check after the move, to see if that move was a winner
        gameOver = False
        winner = None
        if self.board.hasPlayerWon(settings.k, typeInThisGame):
            winner = self.whoseTurn
            gameOver = True

        # make a second check after, to see if that move filled the board
        if not self.board.movesRemain():
            gameOver = True

        # log the move and pass the turn
        self.history.append((moveX, moveY))
        swap = self.whoseTurn
        self.whoseTurn = self.idleTurn
        self.idleTurn = swap

        if gameOver:
            self.endTheGame(winner)

        return gameOver, winner

    # this function handles cleanup after a game concludes, namely alerting the competing agents and doing final logging
    def endTheGame(self, winner):
        if winner == self.xPlayer:
            winnerStr = "X"
        elif winner == self.oPlayer:
            winnerStr = "O"
        else:
            winnerStr = "-"

        # alert the competing agents that the game has concluded, so they can keep their books
        self.whoseTurn.onGameOver()
        self.idleTurn.onGameOver()

        if self.logged:
            textToLog = "\nFinal Board: " + str(self.board) + "\n" + str(self)
            self.gameLog.DoLogText(textToLog)

            self.gameLog.logFile.seek(self.marker - 4) # subtraction is to move backward past the newlines (2x) and the ? character, so only it gets overwritten. windows and mac are OBO from each other...
            self.gameLog.logFile.write(winnerStr)

            self.gameLog.closeLog()

    # This function handles printing games
    def __repr__(self):
        result = "MoveLog:\t" + str(self.history)
        return result
