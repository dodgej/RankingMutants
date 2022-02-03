from agent.AgentBase import AgentBase

# This agent serves as the mechanism allowing humans to battle the agents.
class HumanAgent(AgentBase):
    # this constructor is a little different from the rest since the robots are always ready
    def __init__(self, name):
        AgentBase.__init__(self, name)
        self.publicName = name
        self.isReady = False
        self.desiredMove = None

    # humans become ready by clicking a valid location, which is stored in the desiredMove field
    def makeReady(self, move):
        self.isReady = True
        self.desiredMove = move

    # Responsible for providing the move the human has selected once the simulator asks
    # This function will ONLY be called once the agent is ready, meaning agent will be READY (and have a move stored
    def move(self, board, typeInThisGame, logger):
        textToLog = "-----------------------------------\n"
        textToLog += "Player " + self.privateName + " preparing to make a move, playing " + str(typeInThisGame)
        textToLog += " on this board\n" + str(board)

        self.isReady = False  # having supplied the currently stored move, the agent is no longer ready for the subsequent one
        theMove = self.desiredMove

        self.desiredMove = None
        if logger:
            textToLog = "human move! " + str(self.desiredMove)
            logger.DoLogText(textToLog)
        return theMove
