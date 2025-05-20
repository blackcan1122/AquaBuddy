import sys, time
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore    import QTimer, Qt
from PySide6.QtGui     import QSurfaceFormat

from OpenGL.GL import *
from PIL import Image

class GLWaterWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        fmt = QSurfaceFormat()
        fmt.setVersion(3, 3)
        fmt.setProfile(QSurfaceFormat.CoreProfile)
        QSurfaceFormat.setDefaultFormat(fmt)
        super().__init__(parent)
        self._start = time.time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)  # triggers paintGL
        self.timer.start(16)  # ~60 FPS

    def initializeGL(self):
        # compile shader
        with open(Path(__file__).parent / "assets/shaders/water.frag") as f:
            frag_src = f.read()
        vert_src = """
        #version 330 core
        layout(location = 0) in vec2 aPos;
        out vec2 fragCoord;
        void main() {
            fragCoord = aPos;
            gl_Position = vec4(aPos * 2.0 - 1.0, 0.0, 1.0);
        }
        """
        self.prog = glCreateProgram()
        for src, typ in [(vert_src, GL_VERTEX_SHADER),(frag_src, GL_FRAGMENT_SHADER)]:
            sh = glCreateShader(typ)
            glShaderSource(sh, src)
            glCompileShader(sh)
            if not glGetShaderiv(sh, GL_COMPILE_STATUS):
                raise RuntimeError(glGetShaderInfoLog(sh).decode())
            glAttachShader(self.prog, sh)
        glLinkProgram(self.prog)

        # quad covering [0,1]×[0,1]
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        verts = [-1, -1, 1, -1, 1, 1, -1, 1]
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, (GLfloat * len(verts))(*verts), GL_STATIC_DRAW)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, None)

    def paintGL(self):
        now = time.time() - self._start
        w, h = self.width(), self.height()
        glViewport(0, 0, w, h)
        glClear(GL_COLOR_BUFFER_BIT)

        # draw water
        glUseProgram(self.prog)
        loc_time = glGetUniformLocation(self.prog, "u_time")
        loc_res  = glGetUniformLocation(self.prog, "u_resolution")
        glUniform1f(loc_time, now)
        glUniform2f(loc_res, w, h)
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLE_FAN, 0, 4)

        # # draw fish sprite on top
        # glEnable(GL_TEXTURE_2D)
        # glBindTexture(GL_TEXTURE_2D, self.tex_fish)
        # glBegin(GL_QUADS)
        # # center it, quarter-screen size
        # fw, fh = w * 0.25, h * 0.25
        # cx, cy = w*0.5, h*0.5
        # for dx, dy, sx, sy in [
        #     (-fw, -fh, 0, 0), ( fw, -fh, 1, 0),
        #     ( fw,  fh, 1, 1), (-fw,  fh, 0, 1),
        # ]:
        #     glTexCoord2f(sx, sy)
        #     glVertex2f(cx+dx, cy+dy)
        # glEnd()
        # glDisable(GL_TEXTURE_2D)

    def resizeGL(self, w, h):
        print("pups")
        glViewport(0, 0, w, h)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AquaBuddy Prototype")
        self.setCentralWidget(GLWaterWidget(self))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(800, 600)
    win.show()
    sys.exit(app.exec())