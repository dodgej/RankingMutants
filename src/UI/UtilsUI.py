import wx
import os
from datetime import datetime

from OpenGL.GL import *
import OpenGL.GLUT as GLUT
'''
https://davidmathlogic.com/colorblind/
'''
# colors, for consistency throughout the program
white = [255, 255, 255, 255]
grey = [150, 150, 150, 38]
# the following 8 colors are part of the wong palette from the link above
black = [0, 0, 0, 255]
yellowWong = [240, 228, 66, 220] # used for selection and stuff, so higher alpha

pinkWong = [204, 121, 167, 150]
greenWong = [32, 191, 85, 150]
blueWong = [0, 114, 178, 150]
skyWong = [86, 180, 233, 150]
orangeWong = [230, 159, 0, 150]
vermilionWong = [213, 94, 0, 150]

purple = [148, 55, 255, 150]
brown = [114, 69, 38, 150]
lightGreen = [148, 210, 90, 150]
lavender = [214, 125, 252, 150]
maroon = [179, 57, 81, 150]

dotTXTextension = ".txt"

# helper function that populates the image list with all the icons for agents.
def createImageAndColorList():
    # Useful resource:          https://icoconvert.com/
    imageList = wx.ImageList()
    colorList = []
    nameList = []

    imageList.Create(16, 16, False, 0)

    imageList.Add(wx.Bitmap("assets/blueWong.png"))
    colorList.append(blueWong)
    nameList.append("Blue")

    imageList.Add(wx.Bitmap("assets/greenWong.png"))
    colorList.append(greenWong)
    nameList.append("Green")

    imageList.Add(wx.Bitmap("assets/orangeWong.png"))
    colorList.append(orangeWong)
    nameList.append("Orange")

    imageList.Add(wx.Bitmap("assets/pinkWong.png"))
    colorList.append(pinkWong)
    nameList.append("Pink")

    imageList.Add(wx.Bitmap("assets/vermilionWong.png"))
    colorList.append(vermilionWong)
    nameList.append("Vermilion")

    imageList.Add(wx.Bitmap("assets/skyWong.png"))
    colorList.append(skyWong)
    nameList.append("Sky")


    # Reserve jerseys, in case the programmer puts a LOT of agents into the gym. If this quantity is exceeded, they will be recycled
    imageList.Add(wx.Bitmap("assets/purple.png"))
    colorList.append(purple)
    nameList.append("Purple")
    imageList.Add(wx.Bitmap("assets/brown.png"))
    colorList.append(brown)
    nameList.append("Brown")
    imageList.Add(wx.Bitmap("assets/lightGreen.png"))
    colorList.append(lightGreen)
    nameList.append("Light Green")
    imageList.Add(wx.Bitmap("assets/lavender.png"))
    colorList.append(lavender)
    nameList.append("Lavender")
    imageList.Add(wx.Bitmap("assets/maroon.png"))
    colorList.append(maroon)
    nameList.append("Maroon")

    return imageList, colorList, nameList

# helper function to convert a millisecond time into a time string of the format HH:MM:SS
def timeToString(timeInMilliseconds):
    rawSeconds = max(0, int(timeInMilliseconds / 1000))
    timeSeconds = rawSeconds % 60
    rawMinutes = max(0, int(rawSeconds / 60))
    timeMinutes = rawMinutes % 60
    timeHours = int(rawMinutes / 60) % 60

    outputString = ""
    if timeHours > 0:
        outputString += str(timeHours) + ":"
    outputString += str(timeMinutes) + ":"
    if timeSeconds > 9:
        outputString += str(timeSeconds)
    else:
        outputString += "0" + str(timeSeconds)
    return outputString

# helper function which checks all the filenames in a directory, and returns 1 plus the highest number found, leading to sequentially numbered files
def getNextFileNumber(path, filenameStem):
    sessionNumber = 0
    extantFiles = os.listdir(path)
    for filename in extantFiles:
        if filenameStem in filename:
            thisSessionNumber = int(filename[len(filenameStem):-len(dotTXTextension)])
            if thisSessionNumber > sessionNumber:
                sessionNumber = thisSessionNumber
    return sessionNumber + 1

# responsible for drawing a string at the desired location and paramaterization, but can be arbitrarily scaled
def drawStrokeText(x, y, r, g, b, a, string, font=GLUT.GLUT_STROKE_ROMAN, scale=4):
    glPushMatrix()
    glPushAttrib(GL_CURRENT_BIT)
    glPushAttrib(GL_LINE_BIT)

    glLineWidth(2)
    glTranslate(x,y,0)
    glScalef(.001*scale, .001*scale, .001*scale) # this downscale is needed because the fonts are REALLY big compared to my usual 1 to -1 view volume
    glColor4f(r, g, b, a)

    for character in string:
        #FIXME this is broken on windows :(
        #GLUT.glutStrokeCharacter(font, ord(character))
        glTranslatef(20, 0.0, 0.0)

    glPopAttrib() # line bit
    glPopAttrib() # current bit
    glPopMatrix()

# responsible for drawing a string at the desired location and paramaterization, but is bitmapped, so fixed size
def drawBitmapText(x, y, r, g, b, a, string, font=GLUT.GLUT_BITMAP_HELVETICA_18):
    glPushMatrix()
    glPushAttrib(GL_CURRENT_BIT)

    glColor4f(r, g, b, a)

    glRasterPos2f(x, y)
    for character in string:
        pass# FIXME this is broken on windows :(
        #GLUT.glutBitmapCharacter(font, ord(character))

    glPopAttrib() # current bit
    glPopMatrix()

# logging class, which basically holds a file pointer and includes some assistance with adding timestamps and such
class LogToFile(wx.Log):
    def __init__(self, path, filenameStem, sessionNumber, alsoPrint):
        wx.Log.__init__(self)
        fullLogFilePath = path + filenameStem + str(sessionNumber) + dotTXTextension
        self.logFile = open(fullLogFilePath, mode="w")
        self.alsoPrint = alsoPrint

    def DoLogText(self, message, addTimestamp=False):
        toLogText = ""
        # FIXME this is a little cumbersome, and seems to be built into wx, but I couldnt figure out how to use the LogFormatter
        if addTimestamp:
            now = datetime.now()
            timestamp = now.strftime("%m/%d/%Y-%H:%M:%S")
            toLogText += timestamp + " "
        toLogText += message + "\n"
        if self.alsoPrint:
            print(toLogText, end="")
        self.logFile.write(toLogText)

    def closeLog(self):
        self.logFile.flush()
        os.fsync(self.logFile)
        self.logFile.close()

