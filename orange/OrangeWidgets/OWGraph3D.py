"""
"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtOpenGL

import orange

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import ArrayDatatype
from ctypes import byref, c_char_p, c_int, create_string_buffer
import sys
import numpy
from math import sin, cos

# Import undefined functions, override some wrappers.
try:
    from OpenGL import platform
    gl = platform.OpenGL
except ImportError:
    try:
        gl = cdll.LoadLibrary('libGL.so')
    except OSError:
        from ctypes.util import find_library
        path = find_library('OpenGL')
        gl = cdll.LoadLibrary(path)

glCreateProgram = gl.glCreateProgram
glCreateShader = gl.glCreateShader
glShaderSource = gl.glShaderSource
glCompileShader = gl.glCompileShader
glGetShaderiv = gl.glGetShaderiv
glDeleteShader = gl.glDeleteShader
glDeleteProgram = gl.glDeleteProgram
glGetShaderInfoLog = gl.glGetShaderInfoLog
glGenVertexArrays = gl.glGenVertexArrays
glBindVertexArray = gl.glBindVertexArray
glGenBuffers = gl.glGenBuffers
glDeleteBuffers = gl.glDeleteBuffers
glVertexAttribPointer = gl.glVertexAttribPointer
glEnableVertexAttribArray = gl.glEnableVertexAttribArray
glVertexAttribPointer = gl.glVertexAttribPointer
glEnableVertexAttribArray = gl.glEnableVertexAttribArray
glGetProgramiv = gl.glGetProgramiv


def normalize(vec):
    return vec / numpy.sqrt(numpy.sum(vec** 2))


class OWGraph3D(QtOpenGL.QGLWidget):
    def __init__(self, parent=None):
        QtOpenGL.QGLWidget.__init__(self, QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers), parent)

        self.commands = []
        self.minx = self.miny = self.minz = 0
        self.maxx = self.maxy = self.maxz = 0
        self.b_box = [numpy.array([0,   0,   0]), numpy.array([0, 0, 0])]
        self.camera = numpy.array([0.6, 0.8, 0]) # Location on a unit sphere around the center. This is where camera is looking from.
        self.center = numpy.array([0,   0,   0])

        # TODO: move to center shortcut (maybe a GUI element?)

        self.yaw = self.pitch = 0.
        self.rotation_factor = 100.
        self.zoom_factor = 100.
        self.zoom = 10.
        self.move_factor = 100.
        self.mouse_pos = [100, 100] # TODO: get real mouse position, calculate camera, fix the initial jump

        self.axis_title_font = QFont('Helvetica', 10, QFont.Bold)
        self.ticks_font = QFont('Helvetica', 9)
        self.x_axis_title = ''
        self.y_axis_title = ''
        self.z_axis_title = ''
        self.show_x_axis_title = self.show_y_axis_title = self.show_z_axis_title = True

        self.color_plane = numpy.array([0.95, 0.95, 0.95, 0.3])
        self.color_grid = numpy.array([0.8, 0.8, 0.8, 1.0])

        self.vertex_buffers = []
        self.vaos = []

        self.ortho = False
        self.show_legend = True
        self.legend_border_color = [0.3, 0.3, 0.3, 1]

    def __del__(self):
        glDeleteProgram(self.color_shader)

    def initializeGL(self):
        self.update_axes()
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClearDepth(1.0)
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LINE_SMOOTH)

        self.color_shader = glCreateProgram()
        vertex_shader = glCreateShader(GL_VERTEX_SHADER)
        fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
        self.shaders = [vertex_shader, fragment_shader]

        vertex_shader_source = '''
            attribute vec3 position;
            attribute vec3 offset;
            attribute vec4 color;

            uniform mat4 projection;
            uniform mat4 modelview;
            uniform vec4 overriden_color;
            uniform bool override_color;

            varying vec4 var_color;

            void main(void) {
              //gl_Position = projection * modelview * position;

              // Calculate inverse of rotations (in this case, inverse
              // is actually just transpose), so that polygons face
              // camera all the time.
              mat3 invs;

              invs[0][0] = gl_ModelViewMatrix[0][0];
              invs[0][1] = gl_ModelViewMatrix[1][0];
              invs[0][2] = gl_ModelViewMatrix[2][0];

              invs[1][0] = gl_ModelViewMatrix[0][1];
              invs[1][1] = gl_ModelViewMatrix[1][1];
              invs[1][2] = gl_ModelViewMatrix[2][1];

              invs[2][0] = gl_ModelViewMatrix[0][2];
              invs[2][1] = gl_ModelViewMatrix[1][2];
              invs[2][2] = gl_ModelViewMatrix[2][2];

              vec3 offset_rotated = invs * offset;
              gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * vec4(position+offset_rotated, 1);
              if (override_color)
                  var_color = overriden_color;
              else
                  var_color = color;
            }
            '''

        fragment_shader_source = '''
            varying vec4 var_color;

            void main(void) {
              gl_FragColor = var_color;
            }
            '''

        vertex_shader_source = c_char_p(vertex_shader_source)
        fragment_shader_source = c_char_p(fragment_shader_source)

        def print_log(shader):
            length = c_int()
            glGetShaderiv(shader, GL_INFO_LOG_LENGTH, byref(length))

            if length.value > 0:
                log = create_string_buffer(length.value)
                glGetShaderInfoLog(shader, length, byref(length), log)
                print(log.value)

        length = c_int(-1)
        for shader, source in zip([vertex_shader, fragment_shader],
                                  [vertex_shader_source, fragment_shader_source]):
            glShaderSource(shader, 1, byref(source), byref(length))
            glCompileShader(shader)
            status = c_int()
            glGetShaderiv(shader, GL_COMPILE_STATUS, byref(status))
            if not status.value:
                print_log(shader)
                glDeleteShader(shader)
                return
            else:
                glAttachShader(self.color_shader, shader)

        glBindAttribLocation(self.color_shader, 0, 'position')
        glBindAttribLocation(self.color_shader, 1, 'offset')
        glBindAttribLocation(self.color_shader, 2, 'color')
        glLinkProgram(self.color_shader)
        self.color_shader_override_color = glGetUniformLocation(self.color_shader, 'override_color')
        self.color_shader_overriden_color = glGetUniformLocation(self.color_shader, 'overriden_color')
        linked = c_int()
        glGetProgramiv(self.color_shader, GL_LINK_STATUS, byref(linked))
        if not linked.value:
            print('Failed to link shader!')
        print('Shaders compiled and linked!')

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)

    def paintGL(self):
        glClearColor(1,1,1,1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        width, height = self.width(), self.height()
        divide = self.zoom*10.
        if self.ortho:
            glOrtho(-width/divide, width/divide, -height/divide, height/divide, -1, 1000)
        else:
            aspect = float(width) / height if height != 0 else 1
            gluPerspective(30.0, aspect, 0.1, 100)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        zoom = 100 if self.ortho else self.zoom
        gluLookAt(
            self.camera[0]*zoom + self.center[0],
            self.camera[1]*zoom + self.center[1],
            self.camera[2]*zoom + self.center[2],
            self.center[0],
            self.center[1],
            self.center[2],
            0, 1, 0)
        self.paint_axes()

        glEnable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)

        for cmd, vao in self.commands:
            if cmd == 'scatter':
                glUseProgram(self.color_shader)
                glBindVertexArray(vao.value)
                glUniform1i(self.color_shader_override_color, 0)
                glDrawArrays(GL_TRIANGLES, 0, vao.num_vertices)
                # Draw outlines.
                glUniform1i(self.color_shader_override_color, 1)
                glUniform4f(self.color_shader_overriden_color, 0,0,0,1)
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                glDrawArrays(GL_TRIANGLES, 0, vao.num_vertices)
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                glBindVertexArray(0)
                glUseProgram(0)

        if self.show_legend:
            self.draw_legend()

    def draw_legend(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width(), 0, self.height(), -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glColor4f(*self.legend_border_color)
        glBegin(GL_QUADS)
        glVertex2f(10, 10)
        glVertex2f(10, 100)
        glVertex2f(200, 100)
        glVertex2f(200, 10)
        glEnd()

        glColor4f(1, 1, 1, 1)
        glBegin(GL_QUADS)
        glVertex2f(12, 12)
        glVertex2f(12, 98)
        glVertex2f(198, 98)
        glVertex2f(198, 12)
        glEnd()

    def set_x_axis_title(self, title):
        self.x_axis_title = title
        self.updateGL()

    def set_show_x_axis_title(self, show):
        self.show_x_axis_title = show
        self.updateGL()

    def set_y_axis_title(self, title):
        self.y_axis_title = title
        self.updateGL()

    def set_show_y_axis_title(self, show):
        self.show_y_axis_title = show
        self.updateGL()

    def set_z_axis_title(self, title):
        self.z_axis_title = title
        self.updateGL()

    def set_show_z_axis_title(self, show):
        self.show_z_axis_title = show
        self.updateGL()

    def paint_axes(self):
        zoom = 100 if self.ortho else self.zoom
        cam_in_space = numpy.array([
          self.center[0] + self.camera[0]*zoom,
          self.center[1] + self.camera[1]*zoom,
          self.center[2] + self.camera[2]*zoom
        ])

        def normal_from_points(p1, p2, p3):
            v1 = p2 - p1
            v2 = p3 - p1
            return normalize(numpy.cross(v1, v2))

        def plane_visible(plane):
            normal = normal_from_points(*plane[:3])
            cam_plane = normalize(plane[0] - cam_in_space)
            if numpy.dot(normal, cam_plane) > 0:
                return False
            return True

        def draw_line(line):
            glColor4f(0.2, 0.2, 0.2, 1)
            glLineWidth(2) # Widths > 1 are actually deprecated I think.
            glBegin(GL_LINES)
            glVertex3f(*line[0])
            glVertex3f(*line[1])
            glEnd()

        def draw_values(axis, coord_index, normal, sub=10):
            glColor4f(0.1, 0.1, 0.1, 1)
            glLineWidth(1)
            start = axis[0]
            end = axis[1]
            direction = (end - start) / float(sub)
            middle = (end - start) / 2.
            offset = normal*0.3
            for i in range(sub):
                position = start + direction*i
                glBegin(GL_LINES)
                glVertex3f(*(position-normal*0.08))
                glVertex3f(*(position+normal*0.08))
                glEnd()
                position += offset
                self.renderText(position[0],
                                position[1],
                                position[2],
                                '{0:.2}'.format(position[coord_index]))

        glDisable(GL_DEPTH_TEST)
        glLineWidth(1)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        bb_center = (self.b_box[1] + self.b_box[0]) / 2.

        # Draw axis labels.
        glColor4f(0,0,0,1)
        for axis, title in zip([self.x_axis, self.y_axis, self.z_axis],
                               [self.x_axis_title, self.y_axis_title, self.z_axis_title]):
            middle = (axis[0] + axis[1]) / 2.
            self.renderText(middle[0], middle[1]-0.2, middle[2]-0.2, title,
                            font=self.axis_title_font)

        def draw_axis_plane(axis_plane, sub=10):
            normal = normal_from_points(*axis_plane[:3])
            camera_vector = normalize(axis_plane[0] - cam_in_space)
            cos = numpy.dot(normal, camera_vector)
            cos = max(0.7, cos)
            glColor4f(*(self.color_plane*cos))
            P11, P12, P21, P22 = numpy.asarray(axis_plane)
            glBegin(GL_QUADS)
            glVertex3f(*P11)
            glVertex3f(*P12)
            glVertex3f(*P21)
            glVertex3f(*P22)
            glEnd()
            P22, P21 = P21, P22
            glColor4f(*(self.color_grid * cos))
            Dx = numpy.linspace(0.0, 1.0, num=sub)
            P1vecH = P12 - P11
            P2vecH = P22 - P21
            P1vecV = P21 - P11
            P2vecV = P22 - P12
            glBegin(GL_LINES)
            for i, dx in enumerate(Dx):
                start = P11 + P1vecH*dx
                end = P21 + P2vecH*dx
                glVertex3f(*start)
                glVertex3f(*end)
                start = P11 + P1vecV*dx
                end = P12 + P2vecV*dx
                glVertex3f(*start)
                glVertex3f(*end)
            glEnd()

        planes = [self.axis_plane_xy, self.axis_plane_yz,
                  self.axis_plane_xy_back, self.axis_plane_yz_right]
        visible_planes = map(plane_visible, planes)
        draw_axis_plane(self.axis_plane_xz)
        for visible, plane in zip(visible_planes, planes):
            if not visible:
                draw_axis_plane(plane)

        glEnable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)

        if visible_planes[0]:
            draw_line(self.x_axis)
            draw_values(self.x_axis, 0, numpy.array([0,0,-1]))
        elif visible_planes[2]:
            draw_line(self.x_axis + self.unit_z)
            draw_values(self.x_axis + self.unit_z, 0, numpy.array([0,0,1]))

        if visible_planes[1]:
            draw_line(self.z_axis)
            draw_values(self.z_axis, 2, numpy.array([-1,0,0]))
        elif visible_planes[3]:
            draw_line(self.z_axis + self.unit_x)
            draw_values(self.z_axis + self.unit_x, 2, numpy.array([1,0,0]))

        try:
            rightmost_visible = visible_planes[::-1].index(True)
        except ValueError:
            return
        if rightmost_visible == 0 and visible_planes[0] == True:
            rightmost_visible = 3
        y_axis_translated = [self.y_axis+self.unit_x,
                             self.y_axis+self.unit_x+self.unit_z,
                             self.y_axis+self.unit_z,
                             self.y_axis]
        normals = [numpy.array([1,0,0]),
                   numpy.array([0,0,1]),
                   numpy.array([-1,0,0]),
                   numpy.array([0,0,-1])
                ]
        axis = y_axis_translated[rightmost_visible]
        draw_line(axis)
        normal = normals[rightmost_visible]
        draw_values(y_axis_translated[rightmost_visible], 1, normal)

    def update_axes(self):
        x_axis = [[self.minx, self.miny, self.minz],
                  [self.maxx, self.miny, self.minz]]
        y_axis = [[self.minx, self.miny, self.minz],
                  [self.minx, self.maxy, self.minz]]
        z_axis = [[self.minx, self.miny, self.minz],
                  [self.minx, self.miny, self.maxz]]
        self.x_axis = x_axis = numpy.array(x_axis)
        self.y_axis = y_axis = numpy.array(y_axis)
        self.z_axis = z_axis = numpy.array(z_axis)

        self.unit_x = unit_x = numpy.array([self.maxx - self.minx, 0, 0])
        self.unit_y = unit_y = numpy.array([0, self.maxy - self.miny, 0])
        self.unit_z = unit_z = numpy.array([0, 0, self.maxz - self.minz])
 
        A = y_axis[1]
        B = y_axis[1] + unit_x
        C = x_axis[1]
        D = x_axis[0]

        E = A + unit_z
        F = B + unit_z
        G = C + unit_z
        H = D + unit_z

        self.axis_plane_xy = [A, B, C, D]
        self.axis_plane_yz = [A, D, H, E]
        self.axis_plane_xz = [D, C, G, H]

        self.axis_plane_xy_back = [H, G, F, E]
        self.axis_plane_yz_right = [B, F, G, C]
        self.axis_plane_xz_top = [E, F, B, A]

    def scatter(self, X, Y, Z, c="b", s=5, **kwargs):
        array = [[x, y, z] for x,y,z in zip(X, Y, Z)]
        if isinstance(c, str):
            color_map = {"r": [1.0, 0.0, 0.0, 1.0],
                         "g": [0.0, 1.0, 0.0, 1.0],
                         "b": [0.0, 0.0, 1.0, 1.0]}
            default = [0.0, 0.0, 1.0, 1.0]
            colors = [color_map.get(c, default) for _ in array]
        else:
            colors = c
 
        if isinstance(s, int):
            s = [s for _ in array]

        max, min = numpy.max(array, axis=0), numpy.min(array, axis=0)
        self.b_box = [max, min]
        self.minx, self.miny, self.minz = min
        self.maxx, self.maxy, self.maxz = max
        self.center = (min + max) / 2 
        self.normal_size = numpy.max(self.center - self.b_box[1]) / 100.

        vao = c_int()
        glGenVertexArrays(1, byref(vao))
        glBindVertexArray(vao.value)

        vertex_buffer = c_int()
        glGenBuffers(1, byref(vertex_buffer))
        glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer.value)

        vertex_size = (3+3+4)*4
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, vertex_size, 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, vertex_size, 3*4)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(2, 4, GL_FLOAT, GL_FALSE, vertex_size, 6*4)
        glEnableVertexAttribArray(2)

        vertices = []
        for (x,y,z), (r,g,b,a), size in zip(array, colors, s):
          vertices.extend([x,y,z, -size*self.normal_size,0,0, r,g,b,a])
          vertices.extend([x,y,z, +size*self.normal_size,0,0, r,g,b,a])
          vertices.extend([x,y,z, 0,+size*self.normal_size,0, r,g,b,a])

        # It's important to keep a reference to vertices around,
        # data uploaded to GPU seem to get corrupted otherwise.
        vertex_buffer.vertices = numpy.array(vertices, 'f')
        glBufferData(GL_ARRAY_BUFFER, len(vertices)*4,
          ArrayDatatype.voidDataPointer(vertex_buffer.vertices), GL_STATIC_DRAW)

        glBindVertexArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        vao.num_vertices = len(vertices) / (vertex_size / 4)
        self.vertex_buffers.append(vertex_buffer)
        self.vaos.append(vao)
        self.commands.append(("scatter", vao))
        self.update_axes()
        self.updateGL()

    def mousePressEvent(self, event):
      self.mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
      if event.buttons() & Qt.MiddleButton:
        pos = event.pos()
        dx = pos.x() - self.mouse_pos.x()
        dy = pos.y() - self.mouse_pos.y()
        if QApplication.keyboardModifiers() & Qt.ShiftModifier:
          off_x = numpy.cross(self.camera, [0,1,0]) * (dx / self.move_factor)
          #off_y = numpy.cross(self.camera, [1,0,0]) * (dy / self.move_factor)
          # TODO: this incidentally works almost fine, but the math is wrong and should be fixed
          self.center += off_x
        else:
          self.yaw += dx /  self.rotation_factor
          self.pitch += dy / self.rotation_factor
          self.camera = [
            sin(self.pitch)*cos(self.yaw),
            cos(self.pitch),
            sin(self.pitch)*sin(self.yaw)]
        self.mouse_pos = pos
        self.updateGL()

    def wheelEvent(self, event):
      if event.orientation() == Qt.Vertical:
        self.zoom -= event.delta() / self.zoom_factor
        if self.zoom < 2:
          self.zoom = 2
        self.updateGL()

    def clear(self):
        self.commands = []


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWGraph3D()
    w.show()
 
    from random import random
    rand = lambda: random() - 0.5
    N = 100
    data = orange.ExampleTable("../doc/datasets/iris.tab")
    array, c, _ = data.toNumpyMA()
    import OWColorPalette
    palette = OWColorPalette.ColorPaletteHSV(len(data.domain.classVar.values))
    x = array[:, 0]
    y = array[:, 1]
    z = array[:, 2]
    colors = [palette[int(ex.getclass())] for ex in data]
    colors = [[c.red()/255., c.green()/255., c.blue()/255., 0.8] for c in colors]

    w.scatter(x, y, z, c=colors)
    app.exec_()
