from random import randint
from agent.AgentBase import AgentBase

# This agent simply behaves randomly (within the rules).
class RandomAgent(AgentBase):
    def move(self, board, typeInThisGame, logger):
        openSquares = board.getOpenSquares()
        move = openSquares[randint(0, len(openSquares) - 1)]
        if logger:
            textToLog = "-----------------------------------\n"
            textToLog += "Player " + self.privateName + " preparing to make a move, playing " + str(typeInThisGame)
            textToLog += " on this board\n" + str(board)
            textToLog += "move chosen randomly!" + str(move) + " from options " + str(openSquares)
            logger.DoLogText(textToLog)
        return move
