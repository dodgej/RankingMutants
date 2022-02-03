from PIL import Image
from OpenGL.GL import *

class Font():
    def __init__(self, fileName):
        self.im = Image.open(fileName)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_REPLACE)
        glTexImage2D(GL_TEXTURE_2D,
                     0, GL_RGBA,
                     self.im.size[0], self.im.size[1],
                     0, GL_RGBA, GL_UNSIGNED_BYTE,
                     self.im.tobytes())

        self.CHARS_PER_ROW = 10.0
        self.CHARS_PER_COLUMN = 10.0
        self.letterSizeS = 1 / self.CHARS_PER_ROW
        self.letterSizeT = 1 / self.CHARS_PER_COLUMN
        self.offset = self.letterSizeS / 15

    # FIXME the coordinate systems here aren't correct, but they behave kind of predictably, return to this later
    def drawString(self, theString, x, y, h):
        glEnable(GL_TEXTURE_2D)
        glPushMatrix()
        a = (GLfloat * 16)()
        mvm = glGetFloatv(GL_MODELVIEW_MATRIX, a)
        glTranslatef(-a[3], -a[7], -a[11])
        glScalef(1/a[0], 1/a[5], 1)
        for i in range(len(theString)):
            theChar = theString[i]
            self.drawChar(theChar, x + .5*h*i, y, h)
        glPopMatrix()
        glDisable(GL_TEXTURE_2D)

    # DO NOT CALL THIS FUNCTION, it is just a helper for drawString, which does necessary work
    def drawChar(self, theChar, x, y, h):
        textureLocation = ord(theChar) - 32 # get the ascii value of the character and offset, because the
        if textureLocation < 0 or textureLocation > self.CHARS_PER_ROW * self.CHARS_PER_COLUMN:
            return
    
        gridX = int(textureLocation % self.CHARS_PER_ROW)
        gridY = int(textureLocation / self.CHARS_PER_ROW)
        minTexCoordS = gridX / self.CHARS_PER_ROW + self.offset
        minTexCoordT = gridY / self.CHARS_PER_COLUMN + self.offset
        maxTexCoordS = minTexCoordS + self.letterSizeS - 2 * self.offset
        maxTexCoordT = minTexCoordT + self.letterSizeT - 2 * self.offset
    
        glBegin(GL_QUADS)
        glTexCoord2f(minTexCoordS, maxTexCoordT)
        glVertex3f(x, y, 0)
    
        glTexCoord2f(minTexCoordS, minTexCoordT)
        glVertex3f(x, y + h, 0)
    
        glTexCoord2f(maxTexCoordS, minTexCoordT)
        glVertex3f(x + h, y + h, 0)
    
        glTexCoord2f(maxTexCoordS, maxTexCoordT)
        glVertex3f(x + h, y, 0)
        glEnd()
