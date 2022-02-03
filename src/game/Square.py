from OpenGL.GL import *
from enum import Enum

import UI.UtilsUI as utils

# This class stores the enumerate for the labels of the state of a square
# as well as helper functions to print squares.  These enumerated square types will
# also serve as our player labels.
class Square(Enum):
    OPEN = 0
    X_HAS = 1
    O_HAS = 2

    # this function handles print
    def __repr__(self):
        if self.value == Square.OPEN.value:
            return "-"
        elif self.value == Square.X_HAS.value:
            return "X"
        elif self.value == Square.O_HAS.value:
            return "O"
        else:
            print(self.value)
            print("PANIC!!!! UNKNOWN TYPE in repr")
            return ""

    # this function handles calls to str()
    def __str__(self):
        if self.value == Square.OPEN.value:
            return "-"
        elif self.value == Square.X_HAS.value:
            return "X"
        elif self.value == Square.O_HAS.value:
            return "O"
        else:
            print(self.value)
            print("PANIC!!!! UNKNOWN TYPE in repr")
            return ""

    # this function is responsible for transforming into the local coordinate space of the square, and spitting out an X or O
    @staticmethod
    def emitGeometry(i, j, step, dispListIdx, moveNumber, font):
        offset = .5 * step

        glPushMatrix()

        # put us in a local coordinate system with the CENTER of this square at the origin
        # THEN (order matters here), we scale so that we can draw in the unit box and the offset is enforced
        glTranslate((i + .5) * step, 1 - (j + .5) * step, 0)
        glScale(.5 * (step - offset), .5 * (step - offset), 1)

        if moveNumber > -1 and moveNumber < 9:
            font.drawString(" "+ str(moveNumber+1), .015, .027, .03)
        elif moveNumber > -1:
            font.drawString(str(moveNumber+1), .015, .027, .03)

        # send out the geometry and leave the local coordinate system
        glCallList(dispListIdx)
        glPopMatrix()

    # this function is responsible for transforming into the local coordinate space of the square, and spitting out an X or O, but with a HIGHLIGHT!
    def emitHighlight(self, i, j, step, xColor, oColor, openColor, circleDispListIdx, exDispListIdx, boxDispListIdx,
                      moveNumber, font):
        offset = .5 * step

        # enter a local coordinate system where this square is centered
        glPushMatrix()
        glTranslate((i + .5) * step, 1 - (j + .5) * step, 0)

        # further, enter a coordinate system where this square is scaled to be a unit box (order matters here)
        glPushMatrix()
        glScale(.5 * step, .5 * step, 1)

        # select the right color for the highlighted square
        if self.value == Square.OPEN.value:
            glColor3ubv(openColor[:-1])
        elif self.value == Square.O_HAS.value:
            glColor3ubv(oColor[:-1])
        elif self.value == Square.X_HAS.value:
            glColor3ubv(xColor[:-1])

        # send out the geometry for the highlighted square, then leave that inner coordinate system
        glCallList(boxDispListIdx)
        glPopMatrix()

        # now prepare to (possibly) draw the symbol on top of the highlighted square by switching to white rescaling (with offset this time)
        glColor4ubv(utils.white)
        glScale(.5 * (step - offset), .5 * (step - offset), 1)

        if moveNumber > -1 and moveNumber < 9:
            font.drawString(" "+ str(moveNumber+1), .015, .027, .03)
        elif moveNumber > -1:
            font.drawString(str(moveNumber+1), .015, .027, .03)

        # draw the symbol and leave the outer local coordinate system
        if self.value == Square.O_HAS.value:
            glCallList(circleDispListIdx)
        elif self.value == Square.X_HAS.value:
            glCallList(exDispListIdx)
        glPopMatrix()
