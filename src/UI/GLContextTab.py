from enum import Enum
from math import sin, cos
from copy import deepcopy
import wx
from wx import glcanvas
from OpenGL.GL import *
from OpenGL.GLU import *

from agent.HumanAgent import HumanAgent
from game.Square import Square
from settings import settings
from UI.Font import Font
import UI.UtilsUI as utils

class GameState(Enum):
    SETUP_PHASE = 0
    FIRST_PLAYER_TURN = 1
    SECOND_PLAYER_TURN = 2
    GAME_OVER = 3

# this class is responsible for storing a game between a HOME agent (that resides in the tab), and whatever the opponent is.
# This responsibility primarily entails drawing the game
class GLContextTab(glcanvas.GLCanvas):
    def __init__(self, parent, homeName, homeColor):
        wx.glcanvas.GLCanvas.__init__(self, parent, id=wx.ID_ANY, attribList=None,
                                      pos=wx.DefaultPosition, size= wx.DefaultSize,
                                      style=0, name='GLCanvas', palette=wx.NullPalette)
        self.Bind(wx.EVT_PAINT, self.processPaintEvent)
        self.Bind(wx.EVT_MOTION, self.processMotion)
        self.Bind(wx.EVT_LEFT_DOWN, self.processClick)

        self.homeName = homeName
        self.homeColor = homeColor
        self.game = None
        self.gamestate = GameState.SETUP_PHASE

        self.timeOnTab = wx.StopWatch()
        self.timeOnTab.Pause()

        self.cursor = (0, 0)
        self.isBoardEditable = False

        self.noHitHere = 999999

        self.context = glcanvas.GLContext(self)
        self.SetCurrent(self.context)

        # From here on it is all setting stuff up for GL
        glLineWidth(2)
        glClearColor(1, 1, 1, 1)
        glEnable(GL_BLEND) # being lazy here, and just leaving blending on. The program doesn't draw much, so not a huge deal
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.font = Font("assets/font.png")

        squareSize = self.computeSquareSize(settings.m, settings.n)

        # set up the display list for the grid that makes up the board
        self.boardDispListIdx = glGenLists(1)
        glNewList(self.boardDispListIdx, GL_COMPILE)
        glBegin(GL_LINES)
        for i in range(settings.m + 1):  # plus one so we get a line on both ends of the board
            glVertex2f(i * squareSize, 1)
            glVertex2f(i * squareSize, 1 - settings.n * squareSize)

        for j in range(settings.n + 1):  # plus one so we get a line on both ends of the board
            glVertex2f(0, 1 - j * squareSize)
            glVertex2f(settings.m * squareSize, 1 - j * squareSize)
        glEnd()
        glEndList()

        # set up the display list for the circle
        self.circleDispListIdx = glGenLists(1)
        glNewList(self.circleDispListIdx, GL_COMPILE)
        glBegin(GL_LINE_LOOP)
        angle = 0
        while angle <= 2.0 * 3.14:
            x = sin(angle)
            y = cos(angle)
            glVertex2f(x, y)
            angle += .1  # this controls how "circle-y" it is (with small angles being MORE circle-y)
        glEnd()
        glEndList()

        # set up the display list for the X
        self.exDispListIdx = glGenLists(1)
        glNewList(self.exDispListIdx, GL_COMPILE)
        glBegin(GL_LINES)
        glVertex2f(-1, -1)
        glVertex2f(1, 1)
        glVertex2f(-1, 1)
        glVertex2f(1, -1)
        glEnd()
        glEndList()

        # set up the display list for the box
        self.boxDispListIdx = glGenLists(1)
        glNewList(self.boxDispListIdx, GL_COMPILE)
        glBegin(GL_QUADS)
        glVertex2f(-1, -1)
        glVertex2f(-1, 1)
        glVertex2f(1, 1)
        glVertex2f(1, -1)
        glEnd()
        glEndList()

    # Prepare the viewport as well as projection and modelview matrices for a new draw pass
    @staticmethod
    def setProjection(width, height):
        glViewport(0, 0, int(width), int(height))

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 1, 0, 1, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    # convert pixel coordinates to orthographic ones, (think 1000x800 pixels become a 1x1 box we draw in)
    def convertPixelToOrthoCoords(self, i, j):
        size = self.GetClientSize() # upper left is 0,0, bottom right is X,Y (positive!)
        xVal = i / size[0]
        yVal = (size[1] - j)/size[1]
        return xVal, yVal

    # convert pixel coordinates to board ones, (think 1000x800 pixels become a square on my 4x9 board)
    def convertPixelToBoardCoords(self, i, j):
        size = self.GetClientSize() # upper left is 0,0, bottom right is X,Y (positive!)
        xOrtho = i / size[0]
        yOrtho = j / size[1] # these are now in ortho coords

        squareSize = self.computeSquareSize(settings.m, settings.n)
        xBoard = xOrtho / squareSize
        yBoard = yOrtho / squareSize
        return int(xBoard), int(yBoard)

    # sets aspect ratio via a crappy hack
    @staticmethod
    def computeSquareSize(m, n):
        # Assume a window with aspect ratio 1, pick the dimension that limits board square size and then compute it.
        # There are probably better ideas, but this works.
        return 1.0 / max(m, n)

    # Handle the draw pass from the windowing perspective, then punt to however the scene renders itself (OOP!)
    def processPaintEvent(self, event):
        self.SetCurrent(self.context)
        if not self.context.IsOK():
            print("freak out, context not OK")
            return

        # determine how big our gl context is in physical pixels in the UI.  This weirdness is necessary
        # because apparently retina displays make the windowing system weird and this keeps it out of the OpenGL code
        size = self.GetClientSize()
        windowScale = self.GetContentScaleFactor()
        self.setProjection(size[0]*windowScale, size[1]*windowScale) # This line is the only one that should be needed here...

        self.Show()
        self.Refresh(False)

        # Windowing system stuff done, now we tell GL to prepare a clean framebuffer
        glClear(GL_COLOR_BUFFER_BIT)

        if self.game:
            squareSize = self.computeSquareSize(settings.m, settings.n)

            numMovesToFilter = - settings.controlPanel.moveSlider.GetValue()
            # draw anything the HOME agent (AKA the X player)wishes to draw
            self.game.xPlayer.render(self.game, squareSize, self.font, numMovesToFilter)

            #print(len(self.game.xPlayer.explainer.sortedDataSerieses))
            #print(len(self.game.oPlayer.explainer.sortedDataSerieses))

            # determine the colors of the X and O players
            exColor = self.game.xPlayer.color
            circleColor = self.game.oPlayer.color

            # draw the board
            self.game.board.render(self.boardDispListIdx,
                                   self.circleDispListIdx,
                                   self.exDispListIdx,
                                   self.boxDispListIdx, squareSize,
                                   exColor,
                                   circleColor,
                                   self.game.history,
                                   self.font,
                                   numMovesToFilter)

        #draw the mouse cursor
        glTranslate(self.cursor[0], self.cursor[1],0)
        glColor4ubv(utils.yellowWong)
        glScalef(.02,.02,.02)
        glCallList(self.exDispListIdx)

        # done drawing stuff, swap the buffers so our newly drawn frame is shown!
        self.SwapBuffers()
        event.Skip()

    # handle mouseover highlights of stuff (usually when humans play or edit the board)
    def processMotion(self, event):
        orthoX, orthoY = self.convertPixelToOrthoCoords(event.x, event.y)
        self.cursor = (orthoX, orthoY)

        statusText = "Mouse motion at " + str(event.x) + ", " + str(event.y)
        if self.game:
            oldHighlight = deepcopy(self.game.board.highlighted)
            boardX, boardY = self.convertPixelToBoardCoords(event.x, event.y)
            if self.game.board.moveIsOnBoard(boardX, boardY):
                self.game.board.highlighted = [(boardX, boardY)]
                if oldHighlight != self.game.board.highlighted:
                    statusText += "; On board, highlight shifted from " + str(oldHighlight) + " to " + str(self.game.board.highlighted)
                    settings.frame.setStatusAndLog(statusText)
            else:
                # Nothing is highlighted via direct board highlight (this could change depending where the mouse is over the explanation)
                self.game.board.highlighted = []

                size = self.GetClientSize()
                self.setProjection(size[0], size[1])  #without these lines, the projection matrix is wrong cuz of retina viewport doubling

                viewport = glGetIntegerv(GL_VIEWPORT)
                selectBuffer = glSelectBuffer(1024)

                glRenderMode(GL_SELECT)
                glInitNames()
                glPushName(settings.noHitHere)

                glMatrixMode(GL_PROJECTION)
                glPushMatrix()
                glLoadIdentity()

                pickingPixels = 1
                gluPickMatrix(event.x, (viewport[3]-event.y), pickingPixels, pickingPixels, viewport)
                glOrtho(0, 1, 0, 1, -1, 1)

                # FIXME working here. need to do a select mode rendering pass on the expl
                squareSize = self.computeSquareSize(settings.m, settings.n)
                numMovesToFilter = settings.controlPanel.moveSlider.GetValue()
                self.game.xPlayer.render(self.game, squareSize, self.font, numMovesToFilter)

                glMatrixMode(GL_PROJECTION)
                glPopMatrix()
                glFlush()

                hits = glRenderMode(GL_RENDER)
                for (near,far,names) in hits:
                    for moveLongIdx in names:
                        if moveLongIdx != settings.noHitHere:
                            moveIdxPair = self.game.board.convertActionVecToIdxPair(moveLongIdx)
                            self.game.board.highlighted.append(moveIdxPair)

                if oldHighlight != self.game.board.highlighted:
                    statusText += "; On Explanation, highlight shifted from " + str(oldHighlight) + " to " + str(self.game.board.highlighted)
                    settings.frame.setStatusAndLog(statusText)
        self.processPaintEvent(event)

    # handle a click event. Many are to be ignored, some are moves, some are edits, so its messy :(
    def processClick(self, event):
        statusText = "click at pixel coords (" + str(event.x) + ", " + str(event.y) + ")"

        # if the game does not exist, then this click means to create it
        if not self.game:
            self.game = settings.gym.createGame()
            self.gamestate = GameState.FIRST_PLAYER_TURN
            statusText += "; Created fresh game, no moves made yet"
        else:
            boardX, boardY = self.convertPixelToBoardCoords(event.x, event.y)
            desiredMove = (boardX, boardY)

            # is the click even relevantly positioned so as to require further examination?
            if self.game.board.moveIsOnBoard(boardX, boardY):
                # is the click to be interpreted as EDITING the board
                if self.isBoardEditable:
                    board = self.game.board
                    pieceThere = board.getPiece(boardX, boardY)

                    # cycle through the options with each click
                    if pieceThere == Square.OPEN:
                        board.setPiece(boardX, boardY, Square.X_HAS)
                    elif pieceThere == Square.X_HAS:
                        board.setPiece(boardX, boardY, Square.O_HAS)
                    else:
                        board.setPiece(boardX, boardY, Square.OPEN)
                    statusText += " which is " + str(desiredMove) + "; Changed " + str(pieceThere) + " to " + str(board.getPiece(boardX, boardY))

                # is the click on an open square and is it to be interpreted as a HUMAN PLAYER MOVING?
                elif self.game.board.moveIsLegal(boardX, boardY):
                    moving = self.game.whoseTurn
                    waiting = self.game.idleTurn
                    if isinstance(moving, HumanAgent):
                        moving.makeReady(desiredMove)
                        self.game.board.pendingMove = [desiredMove]
                    elif isinstance(waiting, HumanAgent):
                        waiting.makeReady(desiredMove)
                        self.game.board.pendingMove = [desiredMove]
                    statusText += " which is " + str(desiredMove) + "; Human move bound, press Step or Play to finalize it"

                else:
                    statusText += " which is " + str(desiredMove) + "; Move deemed **ILLEGAL**:"
            else:
                statusText += " which is " + str(desiredMove) + "; Move not on board"

        self.processPaintEvent(event)
        settings.frame.setStatusAndLog(statusText)

    # This function does whatever you want to occur every frame, in this case, move some geometry.
    # It returns whether or not this game has terminated
    def update(self):
        # setup the players and board, then let the first player take their turn
        gameOver = True
        if GameState.SETUP_PHASE == self.gamestate:
            self.game = settings.gym.createGame()
            self.gamestate = GameState.FIRST_PLAYER_TURN
        elif GameState.FIRST_PLAYER_TURN == self.gamestate:
            if self.game:
                gameOver, winner, moveX, moveY = self.game.gameStep() # no verbose for now
            if gameOver:
                self.gamestate = GameState.GAME_OVER
            else:
                self.gamestate = GameState.SECOND_PLAYER_TURN
        elif GameState.SECOND_PLAYER_TURN == self.gamestate:
            if self.game:
                gameOver, winner, moveX, moveY = self.game.gameStep() # no verbose for now
            if gameOver:
                self.gamestate = GameState.GAME_OVER
            else:
                self.gamestate = GameState.FIRST_PLAYER_TURN
        elif GameState.GAME_OVER == self.gamestate:
            self.gamestate = GameState.SETUP_PHASE
            return True
        return False
