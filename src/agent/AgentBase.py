import abc

# This is the abstract base class (hence the use of the abc import) that specifies an agent
class AgentBase:
    __metaclass__ = abc.ABCMeta

    # agents ALL need to know: (1) whether they are playing X or O,
    # (2,3) the board size, (4) sequence length they seek to create, (5) name to identify the agent
    # (6) color to be used in the UI, and (7) readiness
    def __init__(self, name):
        self.privateName = name
        self.publicName = "unboundPublicName"
        self.color = [1, 0, 0, 1]
        self.isReady = True  # all the programmatic agents are always ready as currently programmed (could be attached to a timer)
        self.isLearning = False # all programmatic agents start in mode without learning

    # This specifies that all Agents MUST specify a move function to override this one
    @abc.abstractmethod
    def move(self, board, typeInThisGame, logger):         pass

    # these MAY be overridden, but are initialized to be NO-OPs because most kinds of agents do not need these
    def trainAgainst(self, opponent, board, games, logging):            pass
    def reportOptimalLRRange(self, game, logging):                      pass
    def onNewGame(self):                                                pass
    def onGameOver(self):                                               pass
    def render(self, game, squareSize, font, numMovesToFilter):         pass

    # returns whether or not the load/save was successful, here it fails because there is nothing to load for an abstract base class
    def load(self, path):                         return False
    def save(self, path):                         return False
