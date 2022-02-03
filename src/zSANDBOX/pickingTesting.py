from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *


def pickSquares(button, state, x, y):
    if not state: # this is a mouse-up event. do nothing
        return
    viewport = glGetIntegerv(GL_VIEWPORT)
    selectBuffer = glSelectBuffer(1024)

    glRenderMode(GL_SELECT)
    glInitNames()
    glPushName(0)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    pickingPixels = 5
    gluPickMatrix(x, y, pickingPixels, pickingPixels, viewport)
    gluOrtho2D(-1.0, 1.0, -1.0, 1.0)

    drawSquares()

    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glFlush()

    hits = glRenderMode(GL_RENDER)
    print("processing ", len(hits), " hits...")
    for (near, far, names) in hits:
        print("clicked on object(s) named: ", names)

    glutPostRedisplay()

def drawSquares():
    viewport = glGetFloatv(GL_VIEWPORT)
    print("Viewport: ", viewport)
    projection = glGetFloatv(GL_PROJECTION_MATRIX)
    print("Projection: ", projection)
    modelview = glGetFloatv(GL_MODELVIEW_MATRIX)
    print("Modelview: ", modelview)

    for i in range(3):
        for j in range(3):
            glLoadName(i*3+j)
            glColor3f(i/3.0, j/3.0, 1)
            xCoord = i*2/3-1
            yCoord = j*2/3-1
            glRectf(xCoord, yCoord, xCoord + 2/3, yCoord + 2/3)

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    glViewport(0, 0, 500, 500)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(-1.0, 1.0, -1.0, 1.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    drawSquares()
    glFlush()
    glutSwapBuffers()




glutInit( )
glutInitDisplayMode( GLUT_DOUBLE | GLUT_RGB )
glutInitWindowSize( 500, 500 )
glutInitWindowPosition( 100, 100 )
glutCreateWindow("title" )
glClearColor (0.0, 0.0, 0.0, 0.0)

glutMouseFunc(pickSquares)
glutDisplayFunc( display )
glutMainLoop(  )

