import wx
import wx.adv

from UI.GLContextTab import GLContextTab, GameState
from UI.Gym import Gym
from UI.ControlPanel import ControlPanel
import UI.UtilsUI as utils

from settings import settings

class MNKFrame(wx.Frame):
    def __init__(self, title):
        super(MNKFrame, self).__init__(parent=None, title=title, pos=settings.windowPos, size=settings.windowSize, style=wx.DEFAULT_FRAME_STYLE)

        # set up the application level usage log
        logPath = "../logs/usage/"
        usageFileNameStem = "usage"
        performanceFilenameStem = "perf"
        self.sessionNumber = utils.getNextFileNumber(logPath, usageFileNameStem)
        self.usageLog = utils.LogToFile(logPath, usageFileNameStem, self.sessionNumber, alsoPrint=False)
        performanceLog = utils.LogToFile(logPath, performanceFilenameStem, self.sessionNumber, alsoPrint=True)

        # setup the gym
        settings.gym = Gym(performanceLog)

        # setup the font
        self.fontForWX = self.GetFont()#wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False)
        if not settings.enableDevControls:
            self.fontForWX.SetPointSize(16)

        # setup the status bar
        self.SetMinSize((749, 592))
        self.CreateStatusBar(4)
        self.StatusBar.SetStatusWidths([-1, 100, 150, 150])  # first arg means variable length, rest of args are fixed pixel widths

        # control panel setup
        frameSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(frameSizer)
        self.controlPanel = ControlPanel(self, settings.gym)
        settings.controlPanel = self.controlPanel
        frameSizer.Add(self.controlPanel)
        self.runTabTimers = False

        # set up the frame timer
        self.frameTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.processTimerEvent, self.frameTimer)
        self.baseFrameRate = 1000
        self.frameTimer.Start(self.baseFrameRate)  # This seems to set the framerate

        # notebook setup
        self.nb = wx.Notebook(self, wx.NB_TOP)
        font = self.nb.GetFont()
        self.nb.SetFont(self.fontForWX)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.processPageChange)
        frameSizer.Add(self.nb, 1, wx.EXPAND) # the 1 means it expands in both directions and fills the space
        self.createTabs()

        # bind the function to handle closing the application, to tie off loose ends and report usage statistics
        self.Bind(wx.EVT_CLOSE, self.processClose)

        self.setStatusAndLog("Session " + str(self.sessionNumber) + " initialized")

    def createTabs(self):
        self.imageList, colorList, nameList = utils.createImageAndColorList()
        self.nb.SetImageList(self.imageList)
        robots = settings.gym.getAgentsWithoutHumans()
        numColors = len(colorList)
        for i in range(len(robots)):
            # issue the agent a jersey color and create UI elements accordingly
            agent = robots[i]
            imageAndColorIndex = i % numColors # reuse jersey colors if we run out (sorry, limited supply!)
            agent.color = colorList[imageAndColorIndex]

            if settings.enableNameObfuscation:
                agent.publicName = nameList[imageAndColorIndex]
            else:
                agent.publicName = agent.privateName

            tab = GLContextTab(self.nb, agent.publicName, agent.color)

            self.nb.AddPage(tab, agent.publicName) # FIXME removed the icons for now, they arent appearing in the right places, and are breaking string spacing

        self.processPageChange(None)

    # closes the application, elegantly printing stuff and closing logs
    def processClose(self, event):
        overallTimeUsed = 0
        textToLog = "Session Ended, usage report:\n"
        for tab in self.nb.Children:
            agent = settings.gym.getAgentWithName(tab.homeName)
            overallTimeUsed += tab.timeOnTab.Time()
            textToLog += agent.publicName + " (" + agent.privateName + ") used for " + utils.timeToString(tab.timeOnTab.Time()) + "\n"

        textToLog += "Overall time used: " + utils.timeToString(overallTimeUsed)
        self.setStatusAndLog(textToLog)

        self.Destroy()

    # responsible for setting up the UI in response to a page change (e.g. must be paused, possibly some UI values restored, etc)
    def processPageChange(self, event):
        self.controlPanel.forcePause(event)
        currTab = self.nb.Children[self.nb.GetSelection()]

        # first, start this stopwatch and stop the one we had been using
        stopwatch = currTab.timeOnTab
        if self.runTabTimers:
            stopwatch.Start(stopwatch.Time())
        lastPageNameAndTime = "Nowhere"
        if event:
            lastSelectedTab = self.nb.Children[event.OldSelection]
            lastSelectedTab.timeOnTab.Pause()
            lastAgent = settings.gym.getAgentWithName(lastSelectedTab.homeName)
            lastPageNameAndTime = lastAgent.publicName + " (" + lastAgent.privateName + "), usage " + utils.timeToString(lastSelectedTab.timeOnTab.Time())

        # populate the list of choices in dropdown based on tab
        choices = []
        numColors = self.imageList.GetImageCount()
        for childTab in self.nb.Children:
            if childTab == currTab:
                self.controlPanel.homeLabel.SetLabel(childTab.homeName)
                imageIndex = self.nb.GetSelection() % numColors
                newBitmap = self.imageList.GetBitmap(imageIndex)
                self.controlPanel.homeIcon.SetBitmap(newBitmap)
            else:
                choices += [childTab.homeName]

        # translate the list of strings to the drop down menu
        self.controlPanel.awayComboBox.Set(choices)
        self.controlPanel.awayComboBox.SetSelection(0)
        offset = 0
        for index in range(self.controlPanel.awayComboBox.GetCount()):
            if index == self.nb.GetSelection():
                offset = 1
            bmp = self.imageList.GetBitmap((index+offset) % self.imageList.GetImageCount())
            self.controlPanel.awayComboBox.SetItemBitmap(index, bmp)

        # set up the human special in the drop down (it has a special icon instead of a jersey color)
        if settings.enableHumanPlay:
            penguin = wx.Image('assets/Penguin.jpg', wx.BITMAP_TYPE_JPEG)
            self.controlPanel.awayComboBox.Append('Human', wx.Bitmap(penguin.Scale(16, 16)))
        if event:
            currAgent = settings.gym.getAgentWithName(currTab.homeName)
            textToLog = "Processed a page change to " + currAgent.publicName + " (" + currAgent.privateName + ") from " + lastPageNameAndTime
            self.setStatusAndLog(textToLog)

    # responsible for advancing the simulation to the next state if not paused, and causing a redraw either way (e.g. might have resized window)
    def processTimerEvent(self, event):
        #print(self.GetPosition(), self.GetSize())
        currTab = self.nb.Children[self.nb.GetSelection()]
        if not self.controlPanel.pauseButton.Value:
            if currTab.update() and self.controlPanel.gameOverPauseCheck.Value:  # game ended, pause (maybe)!
                self.controlPanel.forcePause(event)

        # get timer strings together
        overallTimeUsed = 0
        for tab in self.nb.Children:
            overallTimeUsed += tab.timeOnTab.Time()
        stringOverallTime = "Overall timer: " + utils.timeToString(overallTimeUsed)
        stringTabTime = "Tab timer: " + utils.timeToString(currTab.timeOnTab.Time())  # time is in milliseconds

        if currTab.game:
            decisionNumber = len(currTab.game.history)
            stringMoveNumber = "Decision #: " + str(decisionNumber + 1)
            if decisionNumber > 0:
                self.controlPanel.moveSlider.SetMin(-decisionNumber)
                self.controlPanel.moveSlider.Refresh()
        else:
            stringMoveNumber = ""

        self.SetStatusText(stringMoveNumber, 1)  # 1st field is move timer
        self.SetStatusText(stringTabTime, 2) # 2nd field is the tab's timer
        self.SetStatusText(stringOverallTime, 3)  # 3rd field is the OVERALL timer

        # we updated the tab, it needs to be redrawn
        currTab.processPaintEvent(event)

    # responsible for Toggling the state to edit the board
    def processEditToggle(self, event):
        currTab = self.nb.Children[self.nb.GetSelection()]

        currTab.isBoardEditable = not currTab.isBoardEditable
        if currTab.isBoardEditable:
            self.controlPanel.editButton.SetLabel("Stop Editing")
        else:
            self.controlPanel.editButton.SetLabel("Edit the Board")

        statusText = "Board Editing is Toggled, currently " + str(currTab.isBoardEditable)
        self.setStatusAndLog(statusText)

    # responsible for clearing the board
    def processClearButton(self, event):
        self.controlPanel.forcePause(event)
        currTab = self.nb.Children[self.nb.GetSelection()]

        if currTab.game:
            currTab.game.history = []
            currTab.game.board.clearBoard()
            currTab.gamestate = GameState.SETUP_PHASE

            self.setStatusAndLog("Cleared Board")
        else:
            self.setStatusAndLog("No Board to Clear")

    def processKillGame(self, event):
        currTab = self.nb.Children[self.nb.GetSelection()]
        if currTab.game:
            winner = None
            currTab.game.endTheGame(winner)
            currTab.game = None

            self.setStatusAndLog("Killed Game")
        else:
            self.setStatusAndLog("No Game to Kill")

    def processStart(self, event):
        self.setStatusAndLog("Started tab timers")
        self.runTabTimers = True

        currTab = self.nb.Children[self.nb.GetSelection()]
        currTab.timeOnTab.Start(currTab.timeOnTab.Time())

        self.nb.DeleteAllPages()
        settings.enableHumanPlay = False
        settings.enableNameObfuscation = True
        settings.gym.agents = settings.gym.agentsToAssess
        self.createTabs()

        event.GetEventObject().Hide()

    def processDone(self, event):
        #FIXME sort this based on private name, and have the private names start with 1-5?
        agents = []
        for tab in self.nb.Children:
            tab.timeOnTab.Pause()
            agents.append(settings.gym.getAgentWithName(tab.homeName))

        list.sort(agents, key=lambda agent: agent.privateName)
        for agent in agents:
            print(agent.publicName, " has private name\t ", agent.privateName)
        self.setStatusAndLog("DONE with task")

    # responsible for clearing the board
    def processGetBoardID(self, event):
        self.controlPanel.forcePause(event)
        currTab = self.nb.Children[self.nb.GetSelection()]

        if currTab.game:
            boardID = currTab.game.board.getBoardID()
            print("Requested Board ID: ", boardID)

            self.setStatusAndLog("Board ID printed - "+ str(boardID))
        else:
            self.setStatusAndLog("No Board from which to get an ID")

    # responsible for advancing gamestate a single step
    def processStepButton(self, event):
        currTab = self.nb.Children[self.nb.GetSelection()]
        '''
        if currTab.gamestate == GameState.SETUP_PHASE:
            currTab.update() # This call causes the gym to create the game
        '''
        currTab.update()
        '''
        if currTab.gamestate == GameState.GAME_OVER:
            currTab.update() # this call leaves  the gameOver state and be ready to make a move with next step click
        '''

        currTab.processPaintEvent(event)
        self.setStatusAndLog("Single Stepped Move")

    # speed up or slow down the play rate (by restarting the frame timer)
    def processSpeedScroll(self, event):
        sliderValue = self.controlPanel.speedSlider.GetValue()
        self.frameTimer.Start(self.baseFrameRate / sliderValue)
        statusText = "Speed Changed"
        self.setStatusAndLog(statusText)

    # writes a line to the usage log file and updates status text.
    def setStatusAndLog(self, message, messageField=0): # the default is the actual status message (biggest and leftmost)
        self.SetStatusText(message, messageField)
        self.usageLog.DoLogText(message, True)

    # creates a game and then asks the agent to report on learning rates for that game
    def processComputeOptimalLRRange(self, event):
        currTab = self.nb.Children[self.nb.GetSelection()]
        agent = settings.gym.getAgentWithName(currTab.homeName)

        if not currTab.game:
            currTab.game = settings.gym.createGame()

        logging = self.controlPanel.logAllButton.GetValue()
        agent.reportOptimalLRRange(currTab.game)