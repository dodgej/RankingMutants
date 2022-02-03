import wx
import wx.adv

from settings import settings

class ControlPanel(wx.Panel):
    def __init__(self, frame, gym):
        super(ControlPanel, self).__init__(parent=frame)


        self.frame = frame
        self.gym = gym

        self.SetFont(frame.fontForWX)

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(panelSizer)

        # BIG BOX - controls to set the players involved in the game
        playerControlsSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label="Player Controls")
        panelSizer.Add(playerControlsSizer, proportion=1, flag=wx.EXPAND | wx.BOTTOM, border=20)

        # horizontal sizer to contain both static text and bitmap for the HOME player
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        playerControlsSizer.Add(sizer1)
        sizer1.Add(wx.StaticText(self, -1, 'X player'), 0, 0, 0)
        bmp = wx.Bitmap('assets/Penguin.jpg', wx.BITMAP_TYPE_JPEG)
        self.homeIcon = wx.StaticBitmap(self, bitmap=bmp)
        sizer1.Add(self.homeIcon, 0, 0, 0)
        self.homeLabel = wx.StaticText(self, -1, '<agent NAME>')
        sizer1.Add(self.homeLabel, 0, 0, 0)

        # horizontal sizer to contain both the static text and drop down menu (populated later) for the AWAY player
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        playerControlsSizer.Add(sizer2, 1, wx.EXPAND)
        sizer2.Add(wx.StaticText(self, -1, 'O player'), 0, 0, 0)
        self.awayComboBox = wx.adv.BitmapComboBox(self, -1, choices=['<agent NAME>'], size=(150,-1), style=wx.CB_READONLY)
        sizer2.Add(self.awayComboBox, 1, wx.EXPAND)

        # horizontal sizer to contain the static text and button displaying/choosing who goes first
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        playerControlsSizer.Add(sizer3, 1, wx.EXPAND)
        sizer3.Add(wx.StaticText(self, -1, 'Goes first?'))
        self.initiativeButton = wx.ToggleButton(self, -1, 'X Player')
        self.initiativeButton.SetValue(True)
        self.initiativeButton.Bind(wx.EVT_TOGGLEBUTTON, self.processInitiativeToggle)
        sizer3.Add(self.initiativeButton, 1, wx.EXPAND)

        # controls to edit the contents of the board
        boardManipSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label="Board Manipulations")
        panelSizer.Add(boardManipSizer, 1, wx.EXPAND)

        boardSizer = wx.BoxSizer(wx.HORIZONTAL)
        boardManipSizer.Add(boardSizer)
        boardSizer.Add(wx.StaticText(self, -1, 'Initial Board'))
        self.initialBoardComboBox = wx.ComboBox(self, -1, choices=self.gym.getBoardNames(), value="Empty", size=(150,-1), style=wx.CB_READONLY)
        boardSizer.Add(self.initialBoardComboBox)

        editClearSizer = wx.BoxSizer(wx.HORIZONTAL)
        boardManipSizer.Add(editClearSizer)
        self.editButton = wx.ToggleButton(self, -1, 'Edit the Board')
        self.editButton.Bind(wx.EVT_TOGGLEBUTTON, frame.processEditToggle) # handled by the frame since it involves the tabs
        editClearSizer.Add(self.editButton)
        clearButton = wx.Button(self, -1, 'Clear the Board')
        clearButton.Bind(wx.EVT_BUTTON, frame.processClearButton) # handled by the frame since it involves the tabs
        editClearSizer.Add(clearButton)

        IDButton = wx.Button(self, -1, 'Get Board ID')
        IDButton.Bind(wx.EVT_BUTTON, frame.processGetBoardID)  # handled by the frame since it involves the tabs
        boardManipSizer.Add(IDButton)

        if not settings.enableDevControls:
            panelSizer.Hide(boardManipSizer)
            panelSizer.AddStretchSpacer(1)

        # BIG BOX - controls to change playback parameters
        playbackSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label="Playback Controls")
        panelSizer.Add(playbackSizer, proportion=1, flag=wx.EXPAND | wx.BOTTOM, border=20)

        # horizontal sizer containing the play/pause button....
        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        playbackSizer.Add(sizer4, 1, wx.EXPAND)
        self.pauseButton = wx.ToggleButton(self, label="Play")
        self.pauseButton.SetValue(True)
        self.pauseButton.Bind(wx.EVT_TOGGLEBUTTON, self.processPauseToggle)
        sizer4.Add(self.pauseButton, 0, 0, 0)

        # ... and the step button
        stepButton = wx.Button(self, -1, 'Step')
        stepButton.Bind(wx.EVT_BUTTON, frame.processStepButton) # handled by the frame because it involves the tabs
        sizer4.Add(stepButton, 1, wx.EXPAND)

        # next comes the checkbox for pausing at game over
        self.gameOverPauseCheck = wx.CheckBox(self, label="Pause @ Game Over?")
        self.gameOverPauseCheck.SetValue(True)
        playbackSizer.Add(self.gameOverPauseCheck, 0, 0, 0)

        # next comes the speed slider, and its label
        speedSizer = wx.BoxSizer(wx.HORIZONTAL)
        playbackSizer.Add(speedSizer, 1, wx.EXPAND)
        speedSizer.Add(wx.StaticText(self, -1, 'Play Speed'), 0, 0, 0)
        self.speedSlider = wx.Slider(self, maxValue = 1000, minValue=1)
        self.speedSlider.Bind(wx.EVT_SCROLL_THUMBRELEASE, frame.processSpeedScroll) # handled by the frame because it involves timing
        speedSizer.Add(self.speedSlider)
        if not settings.enableDevControls:
            sizer4.Hide(self.pauseButton)
            self.gameOverPauseCheck.Hide()
            playbackSizer.Hide(speedSizer)
            panelSizer.AddStretchSpacer(1)
        playbackSizer.Add(wx.StaticText(self, -1, 'Show Until Move...'), 0, 0, 0)
        self.moveSlider = wx.Slider(self, maxValue = 0, minValue=-1, style=wx.SL_HORIZONTAL)
        self.moveSlider.Bind(wx.EVT_SCROLL_THUMBRELEASE, self.processRewindScroll)
        playbackSizer.Add(self.moveSlider, 1, wx.EXPAND)

        # BIG BOX - controls for EXPLANATION!
        explSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label="Explanation Controls")
        panelSizer.Add(explSizer, proportion=1, flag=wx.EXPAND | wx.BOTTOM, border=20)

        # radio buttons to select a scalar field to visualize (if applicable)
        self.timeExplButton = wx.RadioButton(parent=self, label="Why: Scores Through Time", style=wx.RB_GROUP)
        self.timeExplButton.SetValue(True)
        self.timeExplButton.Bind(wx.EVT_RADIOBUTTON, self.processExplRadioButton)
        explSizer.Add(self.timeExplButton)
        self.smallMultExplButton = wx.RadioButton(parent=self, label="Why: Small Multiples")
        self.smallMultExplButton.Bind(wx.EVT_RADIOBUTTON, self.processExplRadioButton)
        explSizer.Add(self.smallMultExplButton)
        self.sortedExplButton = wx.RadioButton(parent=self, label="Why: Best-to-Worst")
        self.sortedExplButton.Bind(wx.EVT_RADIOBUTTON, self.processExplRadioButton)
        explSizer.Add(self.sortedExplButton)

        # radio buttons to select a scalar field to visualize (if applicable)
        sizer6 = wx.StaticBoxSizer(wx.VERTICAL, self, label="Scalar field to show")
        explSizer.Add(sizer6)
        self.noScoreButton = wx.RadioButton(parent=self, label="none", style=wx.RB_GROUP)
        self.noScoreButton.SetValue(True)
        sizer6.Add(self.noScoreButton, 0, 0, 0)
        self.nnPredictedFinalScoreButton = wx.RadioButton(parent=self, label="predicted final score")
        sizer6.Add(self.nnPredictedFinalScoreButton, 0, 0, 0)
        self.nnPredictedWinPercentButton = wx.RadioButton(parent=self, label="predicted win%")
        sizer6.Add(self.nnPredictedWinPercentButton, 0, 0, 0)
        self.nnPredictedLossPercentButton = wx.RadioButton(parent=self, label="predicted loss%")
        sizer6.Add(self.nnPredictedLossPercentButton, 0, 0, 0)
        self.nnPredictedDrawPercentButton = wx.RadioButton(parent=self, label="predicted draw%")
        sizer6.Add(self.nnPredictedDrawPercentButton, 0, 0, 0)
        '''
        # more of the same, but instead of for the NN predictions, the simulator sampled outcomes
        self.sampledFinalScoreButton = wx.RadioButton(parent=self, label="sampled final score")
        sizer6.Add(self.sampledFinalScoreButton, 0, 0, 0)
        self.sampledWinPercentButton = wx.RadioButton(parent=self, label="sampled win%")
        sizer6.Add(self.sampledWinPercentButton, 0, 0, 0)
        self.sampledLossPercentButton = wx.RadioButton(parent=self, label="sampled loss%")
        sizer6.Add(self.sampledLossPercentButton, 0, 0, 0)
        self.sampledDrawPercentButton = wx.RadioButton(parent=self, label="sampled draw%")
        sizer6.Add(self.sampledDrawPercentButton, 0, 0, 0)
        # and last is the noise, because that is kind of external
        self.noiseButton = wx.RadioButton(parent=self, label="noise")
        sizer6.Add(self.noiseButton, 0, 0, 0)
        '''

        if not settings.enableDevControls:
            explSizer.Hide(sizer6)

        # BIG BOX - controls for Devs ONLY!
        devSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label="Developer Controls")
        panelSizer.Add(devSizer, proportion=1, flag=wx.EXPAND | wx.BOTTOM, border=20)

        # sizer to hold load and save buttons
        sizer8 = wx.BoxSizer(wx.HORIZONTAL)
        devSizer.Add(sizer8)
        loadButton = wx.Button(self, -1, 'Load Agent')
        loadButton.Bind(wx.EVT_BUTTON, self.processLoadAgent)
        sizer8.Add(loadButton, 0, 0, 0)
        saveButton = wx.Button(self, -1, 'Save Agent')
        saveButton.Bind(wx.EVT_BUTTON, self.processSaveAgent)
        sizer8.Add(saveButton, 0, 0, 0)

        # sizer to hold the train headless buttons
        sizer9 = wx.BoxSizer(wx.HORIZONTAL)
        devSizer.Add(sizer9)
        trainHeadlessButton = wx.Button(self, -1, 'Training')
        trainHeadlessButton.Bind(wx.EVT_BUTTON, gym.processTrainHeadless)
        sizer9.Add(trainHeadlessButton, 0, 0, 0)
        sizer9.Add(wx.StaticText(self, -1, 'Games'))
        self.numGamesToTrainSpin = wx.SpinCtrlDouble(self, -1, size=(90,-1), max=10000000, initial=100, inc=10)
        sizer9.Add(self.numGamesToTrainSpin, 0, 0, 0)

        # sizer to hold the rankingBattle buttons
        sizer10 = wx.BoxSizer(wx.HORIZONTAL)
        devSizer.Add(sizer10)
        rankingBattleButton = wx.Button(self, -1, 'Ranking')
        rankingBattleButton.Bind(wx.EVT_BUTTON, self.processRankingBattle)
        sizer10.Add(rankingBattleButton, 0, 0, 0)
        sizer10.Add(wx.StaticText(self, -1, 'Games'))
        self.numGamesToTestSpin = wx.SpinCtrlDouble(self, -1, size=(90, -1),  max=10000000, initial=100, inc=10)
        sizer10.Add(self.numGamesToTestSpin, 0, 0, 0)

        # sizer to hold the rollout type buttons
        sizer11 = wx.BoxSizer(wx.HORIZONTAL)
        devSizer.Add(sizer11)
        sizer11.Add(wx.StaticText(self, -1, 'Rollouts'))
        self.randomRolloutButton = wx.RadioButton(parent=self, label="Random", style=wx.RB_GROUP)
        self.randomRolloutButton.SetValue(True)
        sizer11.Add(self.randomRolloutButton, 0, 0, 0)
        policyRolloutButton = wx.RadioButton(parent=self, label="Policy")
        sizer11.Add(policyRolloutButton, 0, 0, 0)

        # sizer to hold the logging buttons
        sizer12 = wx.BoxSizer(wx.HORIZONTAL)
        devSizer.Add(sizer12)
        sizer12.Add(wx.StaticText(self, -1, 'Logging'))
        self.logAllButton = wx.RadioButton(parent=self, label="All", style=wx.RB_GROUP)
        self.logAllButton.SetValue(True)
        sizer12.Add(self.logAllButton, 0, 0, 0)
        logNothingButton = wx.RadioButton(parent=self, label="Nothing")
        sizer12.Add(logNothingButton, 0, 0, 0)

        # the button to compute the LR range
        lrRangeButton = wx.Button(self, -1, 'Compute Optimal LR Range')
        lrRangeButton.Bind(wx.EVT_BUTTON, self.frame.processComputeOptimalLRRange)
        devSizer.Add(lrRangeButton, 0, 0, 0)

        # the button to create noisified versions of the currently selected agent
        noisifyButton = wx.Button(self, -1, 'Noisify This Agent')
        noisifyButton.Bind(wx.EVT_BUTTON, self.gym.processNoisifyButton)
        devSizer.Add(noisifyButton, 0, 0, 0)

        # instead participants get some other buttons
        if not settings.enableDevControls:
            panelSizer.Hide(devSizer)
            panelSizer.AddStretchSpacer(1)

            # BIG BOX - controls for Devs ONLY!
            participantsSizer = wx.StaticBoxSizer(wx.VERTICAL, self, label="Ignore Until Requested")
            panelSizer.Add(participantsSizer, proportion=1, flag=wx.EXPAND | wx.BOTTOM, border=20)

            startButton = wx.Button(self, -1, 'Start!')
            startButton.Bind(wx.EVT_BUTTON, frame.processStart)
            participantsSizer.Add(startButton)
            killButton = wx.Button(self, -1, 'Kill this game')
            killButton.Bind(wx.EVT_BUTTON, frame.processKillGame)
            participantsSizer.Add(killButton)
            doneButton = wx.Button(self, -1, 'Done!')
            doneButton.Bind(wx.EVT_BUTTON, frame.processDone)
            participantsSizer.Add(doneButton)

        # log control
        log = wx.TextCtrl(self, wx.ID_ANY, size=(300,150), style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL)
        newFont = log.GetFont()
        newFont.SetFractionalPointSize(8)
        log.SetFont(newFont)
        logSizer = wx.BoxSizer(wx.HORIZONTAL)
        panelSizer.Add(logSizer)
        logSizer.Add(log, 1, wx.EXPAND)
        #sys.stdout = log
        #FIXME still working on this routing channel
        panelSizer.Hide(logSizer)

        self.Fit()

    def processExplRadioButton(self, event):
        statusText = "Processed an explanation change to " + event.GetEventObject().GetLabel()
        self.frame.setStatusAndLog(statusText)

    def processRewindScroll(self, event):
        statusText = "rewound to decision " + str(event.GetEventObject().GetValue())
        self.frame.setStatusAndLog(statusText)

    # really only necessary to change the text on the initiative button
    def processInitiativeToggle(self, event):
        if self.initiativeButton.Value:
            self.initiativeButton.SetLabel("X Player")
        else:
            self.initiativeButton.SetLabel("O Player")

        statusText = "Processed an initiative toggle"
        self.frame.setStatusAndLog(statusText)

    # really only necessary to change the text on the play/pause button
    def processPauseToggle(self, event):
        if self.pauseButton.Value:
            self.pauseButton.SetLabel("Play")
        else:
            self.pauseButton.SetLabel("Pause")

        statusText = "Processed a (possibly programmatic) pause toggle"
        self.frame.setStatusAndLog(statusText)

    # pause, but without toggling (i.e. after this returns, the game is paused, goddamnit)
    def forcePause(self, event):
        if not self.pauseButton.Value:
            self.pauseButton.Value = True
            self.processPauseToggle(event)

    # functions to save/load agent parameters
    def processLoadAgent(self, event):
        agent = self.gym.getAgentWithName(self.homeLabel.Label)
        statusText = agent.publicName

        dlgTitle = "Open agent file"
        dlgWildCard = "pyTorch files (*.pth)|*.pth"
        fileDialog = wx.FileDialog(self, dlgTitle, wildcard=dlgWildCard, style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        if fileDialog.ShowModal() == wx.ID_CANCEL:
            statusText += " load was cancelled"
        else:
            pathname = fileDialog.GetPath()
            if agent.load(pathname):
                statusText += " has been loaded."
            else:
                statusText += " could not be loaded."
        self.frame.setStatusAndLog(statusText)

    def processSaveAgent(self, event):
        agent = self.gym.getAgentWithName(self.homeLabel.Label)
        statusText = agent.publicName

        dlgTitle = "Save agent file"
        dlgWildCard = "pyTorch files (*.pth)|*.pth"
        fileDialog = wx.FileDialog(self, dlgTitle, wildcard=dlgWildCard,style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        if fileDialog.ShowModal() == wx.ID_CANCEL:
            statusText += " save was cancelled"
        else:
            pathname = fileDialog.GetPath()
            if agent.save(pathname):
                statusText += " has been saved."
            else:
                statusText += " could not be saved."
        self.frame.setStatusAndLog(statusText)

    # performs a ranking battle between the agents in the gym
    def processRankingBattle(self, event):
        gamesToTest = self.numGamesToTestSpin.GetValue()
        # Alert the user (and logs) that a longrunning process has started
        statusText = "Ranking battle initiated, with " + str(gamesToTest) + " games per matchup..."
        self.frame.setStatusAndLog(statusText)
        #FIXME I havent been able to get the screen to redraw without kicking back to the main event loop.
        #  I do NOT want to do this, because it makes control flow way more complicated, even if we just use a helper fn
        # However, logging this still has value because it lets me time the ranking battle in the logs. Multi-threading is
        # another possible option, but adds significant complexity

        # do the ranking battle!
        participants = self.gym.rankingBattle(gamesToTest)

        # alert the user (and logs) that it is done
        statusText = "Ranking battle complete! Participants: "
        for agent in participants:
            statusText += agent.publicName + " ("+ agent.privateName +  "), "
        self.frame.setStatusAndLog(statusText)
