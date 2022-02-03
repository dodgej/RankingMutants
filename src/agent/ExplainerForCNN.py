from copy import deepcopy
from OpenGL.GL import *

import UI.UtilsUI as utils
from settings import settings
from game.Square import Square

class ExplainerForCNN:
    def __init__(self):

        # these are scalar fields for visualizing what is going on inside the agent
        self.nnPredictedFinalScoreSF = None
        self.nnPredictedWinPercentSF = None
        self.nnPredictedLossPercentSF = None
        self.nnPredictedDrawPercentSF = None
        # more of the same, but instead of for the NN predictions, the simulator sampled outcomes
        self.sampledFinalScoreSF = None
        self.sampledWinPercentSF = None
        self.sampledLossPercentSF = None
        self.sampledDrawPercentSF = None

        self.noiseSF = None

        #data series(es) for visualization
        self.sortedDataSerieses = []
        self.unsortedDataSerieses = []
        self.criticalities = []

    def clearData(self):
        # clear the data series(es) for visualization
        self.sortedDataSerieses = []
        self.unsortedDataSerieses = []
        self.criticalities = []

    # these are used as functors to be sure the fields get stuck in the right place for later retrieval
    def unpackToPredictions(self, fields):
        self.nnPredictedFinalScoreSF = fields[0]
        self.nnPredictedWinPercentSF = fields[1]
        self.nnPredictedLossPercentSF = fields[2]
        self.nnPredictedDrawPercentSF = fields[3]

    def unpackToSampled(self, fields):
        self.sampledFinalScoreSF = fields[0]
        self.sampledWinPercentSF = fields[1]
        self.sampledLossPercentSF = fields[2]
        self.sampledDrawPercentSF = fields[3]

    def captureQValues(self, qValues, board):
        self.unsortedDataSerieses.append(qValues)
        moveIndices = []
        for i in range(len(qValues)):
            moveIndices.append(board.convertActionVecToIdxPair(i))
        sortedQValues = list(zip(deepcopy(qValues), moveIndices))
        sortedQValues.sort(reverse=True, key=lambda tup: tup[0])
        self.sortedDataSerieses.append(sortedQValues)
        criticality = sortedQValues[0][0] - sum(qValues) / len(qValues)
        self.criticalities.append(criticality)

    def renderCoordinateAxes(self):
        renderMode = glGetIntegerv(GL_RENDER_MODE)
        if renderMode == GL_RENDER:
            ticklength = .025

            glBegin(GL_LINES)
            glVertex2f(-1, 0) # Y-axis
            glVertex2f(1, 0)

            yMin = -100
            yMax = 100
            glVertex2f(-1, yMin) # X-axis
            glVertex2f(-1, yMax)

            tickSpacing = 10
            for i in range(yMin, yMax+1, tickSpacing):
                if i == 0:
                    continue
                elif i % 50 == 0:
                    glVertex2f(-1, i)  # a tick
                    glVertex2f(-1 - ticklength * 2, i)
                else:
                    glVertex2f(-1, i)  # a tick
                    glVertex2f(-1 - ticklength, i)

            glEnd()

    def renderScoresThroughTime(self, game, font, highlightedMoves, numMovesToFilter):
        alphaVal = .3
        dataStepSizeX = 4.0 / (settings.m * settings.n)
        didOpponentGoFirst = game.whoWentFirst() == game.oPlayer
        dataStepSizeY = dataStepSizeX * 10
        offset = 1 + int(didOpponentGoFirst)
        lastMoveMine = (len(game.history) % 2 and not didOpponentGoFirst) or ((len(game.history) + 1) % 2 and didOpponentGoFirst)
        numSeries = len(self.unsortedDataSerieses) - (numMovesToFilter + int (lastMoveMine)) // 2
        for d in range(numSeries):
            moveNum = d * 2 + offset
            moveNumStr = str(moveNum)
            if len(moveNumStr) == 1:
                moveNumStr = " " + moveNumStr
            font.drawString(moveNumStr, -.4625 + .465 * d / settings.m, -.255, .0125)

            try:
                series = self.unsortedDataSerieses[d]
            except:
                print("bad access in STT", d, len(self.unsortedDataSerieses))
                continue
            for i in range(len(series)):
                moveIdxPair = game.board.convertActionVecToIdxPair(i)
                piece = game.board.getPiece(moveIdxPair[0], moveIdxPair[1])
                historyIdx = d*2 + offset - 1
                try:
                    moveInHistory = game.history[historyIdx]
                except:
                    moveInHistory = (-1,-1) # load an impossible move
                    print("Attempted to index out of bounds at ", historyIdx, " where up to ", len(game.history), " was allowed.", d, offset, piece, moveIdxPair, i)
                if moveIdxPair in highlightedMoves:
                    glColor4ubv(utils.yellowWong)
                elif piece == Square.X_HAS and moveIdxPair == moveInHistory:
                    glColor4ubv(game.xPlayer.color)
                else:
                    glColor4ubv(utils.grey)

                dataVal = series[i]
                glLoadName(i)
                glBegin(GL_QUADS)
                glVertex2f(-1 + d * dataStepSizeX, dataVal)
                glVertex2f(-1 + (d + .5) * dataStepSizeX, dataVal)
                glVertex2f(-1 + (d + .5) * dataStepSizeX, dataVal + dataStepSizeY)
                glVertex2f(-1 + d * dataStepSizeX, dataVal + dataStepSizeY)
                glEnd()



            '''
            # draw the criticality
            criticality = self.criticalities[d] * .5 # here the taking half will keep it on the chart range
            glColor4f(.1, 0, .6, 1)
            glBegin(GL_QUADS)
            glVertex2f(-1 + d * dataStepSizeX, criticality)
            glVertex2f(-1 + (d + .5) * dataStepSizeX, criticality)
            glVertex2f(-1 + (d + .5) * dataStepSizeX, criticality + dataStepSizeY)
            glVertex2f(-1 + d * dataStepSizeX, criticality + dataStepSizeY)
            glEnd()
            '''

        font.drawString("Time", 0, -.28, .03)

    def renderScoresBestToWorst(self, game, font, highlightedMoves, numMovesToFilter):
        dataStepSizeX = 4.0 / (settings.m * settings.n)
        dataStepSizeY = dataStepSizeX * 20
        dataStepSizeX /= 2
        didOpponentGoFirst = game.whoWentFirst() == game.oPlayer
        lastMoveMine = (len(game.history) % 2 and not didOpponentGoFirst) or ((len(game.history) + 1) % 2 and didOpponentGoFirst)
        numSeries = len(self.unsortedDataSerieses) - (numMovesToFilter + int (lastMoveMine)) // 2
        for d in range(numSeries):
            try:
                series = self.sortedDataSerieses[d]
            except:
                print("bad access in BTW", d, len(self.unsortedDataSerieses))
                continue
            for i in range(len(series)):
                dataVal = series[i][0]
                moveIndices = series[i][1]

                alphaVal = int((1 + d) / numSeries * 255)
                if moveIndices in highlightedMoves:
                    transparentColor = [utils.yellowWong[0], utils.yellowWong[1], utils.yellowWong[2], alphaVal]
                    glLoadName(settings.noHitHere)
                elif d == numSeries - 1:
                    transparentColor = [game.xPlayer.color[0], game.xPlayer.color[1], game.xPlayer.color[2], alphaVal]
                    glLoadName(moveIndices[1] * settings.m + moveIndices[0])
                else:
                    transparentColor = [utils.grey[0], utils.grey[1], utils.grey[2], alphaVal]
                    glLoadName(settings.noHitHere)

                glColor4ubv(transparentColor)

                glBegin(GL_QUADS)
                glVertex2f(-1 + i * dataStepSizeX, dataVal)
                glVertex2f(-1 + (i + .5) * dataStepSizeX, dataVal)
                glVertex2f(-1 + (i + .5) * dataStepSizeX, dataVal + dataStepSizeY)
                glVertex2f(-1 + i * dataStepSizeX, dataVal + dataStepSizeY)
                glEnd()

        font.drawString("Best-to-Worst Moves", 0, -.28, .03)

    def renderSmallMultiples(self, squareSize, game, font, highlightedMoves, numMovesToFilter):
        dataStepSizeX = 4.0 / (settings.m * settings.n)
        dataStepSizeY = dataStepSizeX * 80
        didOpponentGoFirst = game.whoWentFirst() == game.oPlayer
        lastMoveMine = (len(game.history) % 2 and not didOpponentGoFirst) or ((len(game.history) + 1) % 2 and didOpponentGoFirst)
        numSeries = len(self.unsortedDataSerieses) - (numMovesToFilter + int (lastMoveMine)) // 2
        offset = 1 + int(game.whoWentFirst() == game.oPlayer)
        totalMoves = len(game.history)
        for j in range(settings.n):
            for i in range(settings.m):
                # enter a local coordinate system where this square is centered
                glPushMatrix()
                glTranslate((i + .5) * 2.0625 * squareSize - 1, 1 - (j + .5) * 4.5 * squareSize, 0)
                glScalef(squareSize, 2 * squareSize, 1)
                glScalef(.97, .97, 1)
                glScalef(1, .01, 1)  # scale such that the Y-axis ranges -100 to 100

                try:
                    moveNumber = game.history.index((i, j))
                except:
                    moveNumber = -2

                renderMode = glGetIntegerv(GL_RENDER_MODE)
                # draw the chart outlines and axes
                piece = game.board.getPiece(i, j)
                if (i,j) in highlightedMoves:
                    glLineWidth(6)
                    playerColor = utils.yellowWong
                elif piece == Square.X_HAS and moveNumber < totalMoves - numMovesToFilter:
                    glLineWidth(6)
                    playerColor = game.xPlayer.color
                elif piece == Square.O_HAS and moveNumber < totalMoves - numMovesToFilter:
                    glLineWidth(6)
                    playerColor = game.oPlayer.color
                else:
                    glLineWidth(2)
                    playerColor = utils.black

                glColor3ubv(playerColor[:-1])


                if renderMode == GL_SELECT:
                    glLoadName(j * settings.m + i)
                    glBegin(GL_QUADS)
                else:
                    glBegin(GL_LINES)
                glVertex2f(-1, -100)
                glVertex2f(-1, 100)
                glVertex2f(1, 100)
                glVertex2f(1, -100)
                glVertex2f(-1, -100)
                glVertex2f(1, -100)
                glVertex2f(-1, 100)
                glVertex2f(1, 100)
                glEnd()

                if renderMode == GL_RENDER:
                    glLineWidth(2)
                    glColor4ubv(utils.black)
                    glBegin(GL_LINES)
                    glVertex2f(-1, 0)
                    glVertex2f(1, 0)
                    glEnd()

                    actionLongIndex = i + j * settings.m  # inverse of the function in the board converting pair to long index
                    # draw the data
                    for d in range(numSeries):
                        if d == (moveNumber - offset + 1) // 2 and piece == Square.X_HAS:
                            glColor3ubv(playerColor[:-1])
                        else:
                            glColor3ubv(utils.grey[:-1])
                        try:
                            dataVal = self.unsortedDataSerieses[d][actionLongIndex]
                        except:
                            continue
                        glBegin(GL_QUADS)
                        glVertex2f(-1 + d * dataStepSizeX, dataVal)
                        glVertex2f(-1 + (d + .5) * dataStepSizeX, dataVal)
                        glVertex2f(-1 + (d + .5) * dataStepSizeX, dataVal + dataStepSizeY)
                        glVertex2f(-1 + d * dataStepSizeX, dataVal + dataStepSizeY)
                        glEnd()


                glPopMatrix()
                if renderMode == GL_RENDER:
                    for n in range(settings.n):
                        # .245
                        font.drawString("100% W", -.505, .24 - .5175 * n / settings.n,
                                        .0125)  # FIXME shouldnt have to be hand tuned like this, but alas
                        font.drawString("100% L", -.505, .1375 - .5175 * n / settings.n, .0125)
                    for m in range(settings.m):
                        font.drawString("Time", -.425 + .955 * m / settings.m, -.27, .0125)
                        for d in range(numSeries):
                            moveNum = d * 2 + offset
                            moveNumStr = str(moveNum)
                            if len(moveNumStr) == 1:
                                moveNumStr = " " + moveNumStr
                            font.drawString(moveNumStr, -.4625 + .955 * m / settings.m + d/(settings.m*settings.n)*.2, -.255, .004)

    def render(self, game, squareSize, rewardGameWin, penaltyGameLoss, font, numMovesToFilter):
        '''
        viewport = glGetFloatv(GL_VIEWPORT)
        print("Viewport: ", viewport)
        projection = glGetFloatv(GL_PROJECTION_MATRIX)
        print("Projection: ", projection)
        modelview = glGetFloatv(GL_MODELVIEW_MATRIX)
        print("Modelview: ", modelview)
        '''

        #board bottom edge X
        bottomEdgeY = 1-settings.n*squareSize
        screenBottom = 0

        chartCenterY = .5*bottomEdgeY-screenBottom
        chartCenterX = .5*settings.m*squareSize

        glPushMatrix()
        glTranslate(chartCenterX, chartCenterY, 0)
        glScalef(.93, .93, 1) # shrink a bit so we have a border
        glScalef(chartCenterX, chartCenterY, 1)  # make so the pixel space is replaced by 0-1 space

        if settings.controlPanel.smallMultExplButton.GetValue():
            self.renderSmallMultiples(squareSize, game, font, game.board.highlighted, numMovesToFilter)
        else: # the other two visuals use same coordinate axes
            glScalef(1,.94,1) # Give a little more space for text
            glScalef(1, .01, 1)  # scale such that the Y-axis ranges -100 to 100
            glColor4ubv(utils.black)
            self.renderCoordinateAxes()

            font.drawString("100% Win", -.5, .255, .03) #FIXME shouldnt have to be hand tuned like this, but alas
            font.drawString("100% Loss", -.5, -.28, .03)

        if settings.controlPanel.timeExplButton.GetValue():
            self.renderScoresThroughTime(game, font, game.board.highlighted, numMovesToFilter)

        if settings.controlPanel.sortedExplButton.GetValue():
            self.renderScoresBestToWorst(game, font, game.board.highlighted, numMovesToFilter)

        glPopMatrix()


        # now draw whatever scalar fields we want
        SFtoDraw = None
        maxScore = 1
        minScore = 0
        scoreRange = maxScore - minScore
        if settings.controlPanel.nnPredictedFinalScoreButton.GetValue():
            SFtoDraw = self.nnPredictedFinalScoreSF
            maxScore = rewardGameWin
            minScore = penaltyGameLoss
            scoreRange = maxScore - minScore
        if settings.controlPanel.nnPredictedWinPercentButton.GetValue():
            SFtoDraw = self.nnPredictedWinPercentSF
        if settings.controlPanel.nnPredictedLossPercentButton.GetValue():
            SFtoDraw = self.nnPredictedLossPercentSF
        if settings.controlPanel.nnPredictedDrawPercentButton.GetValue():
            SFtoDraw = self.nnPredictedDrawPercentSF
        '''
        if settings.controlPanel.sampledFinalScoreButton.GetValue():
            SFtoDraw = self.sampledFinalScoreSF
            maxScore = rewardGameWin
            minScore = penaltyGameLoss
            scoreRange = maxScore - minScore
        if settings.controlPanel.sampledWinPercentButton.GetValue():
            SFtoDraw = self.sampledWinPercentSF
        if settings.controlPanel.sampledLossPercentButton.GetValue():
            SFtoDraw = self.sampledLossPercentSF
        if settings.controlPanel.sampledDrawPercentButton.GetValue():
            SFtoDraw = self.sampledDrawPercentSF
        if settings.controlPanel.noiseButton.GetValue():
            SFtoDraw = self.noiseSF
        '''


        if not SFtoDraw:
            return

        for j in range(settings.n):
            for i in range(settings.m):
                alpha = SFtoDraw.getScalar(i, j) - minScore
                alpha = max(alpha, 0)
                alpha /= scoreRange
                alpha = min(alpha, 1)

                if alpha < .5:
                    glColor3f(1,alpha*2,alpha*2)
                else:
                    glColor3f(1-(alpha-.5)*2,1-(alpha-.5)*2,1)

                glBegin(GL_QUADS)

                glVertex2f(i    *squareSize, 1 -   j  *squareSize)
                glVertex2f((i+1)*squareSize, 1 -   j  *squareSize)
                glVertex2f((i+1)*squareSize, 1 - (j+1)*squareSize)
                glVertex2f(i    *squareSize, 1 - (j+1)*squareSize)
                glEnd()