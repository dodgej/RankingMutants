class Settings:
    def __init__(self):
        # enable/disable features
        self.enableDevControls = False
        self.enableHumanPlay = True
        self.enableNameObfuscation = True

        self.runTimers = False

        # stuff about the window
        self.windowSize = (1230, 776)
        self.windowPos = (50, 24)

        # various pointers to help things access stuff they need
        self.controlPanel = None
        self.gym = None
        self.frame = None

        self.noHitHere = 99999
        self.numOutcomes = 3  # win, loss, draw, expressed as a %

        # board size
        #self.m = 12
        #self.n = 5
        #self.k = 5

        #self.m = 9
        #self.n = 9
        #self.k = 4

        self.m = 9
        self.n = 4
        self.k = 4

        #self.m = 3
        #self.n = 3
        #self.k = 3


settings = Settings()
