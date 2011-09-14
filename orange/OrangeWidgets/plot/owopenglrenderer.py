'''

#################
OpenGL Renderer (``owopenglrenderer``)
#################

.. autoclass:: OrangeWidgets.plot.OWOpenGLRenderer

'''

from ctypes import c_void_p

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtOpenGL

import OpenGL
OpenGL.ERROR_CHECKING = False
OpenGL.ERROR_LOGGING = False
OpenGL.FULL_LOGGING = False
OpenGL.ERROR_ON_COPY = False
from OpenGL.GL import *
from OpenGL.GL.ARB.vertex_array_object import *
from OpenGL.GL.ARB.vertex_buffer_object import *
import numpy

class VertexBuffer:
    '''
    An abstraction simplifying the usage of Vertex Buffer Objects (VBO). Warning: understanding what this class does
    requires basic knowledge of OpenGL.

    VBOs are necessary in OpenGL 2+ world, since immediate mode (glBegin/glVertex/glEnd paradigm) has been deprecated
    and is slow (even more so using it through PyOpenGL). Vertex Array Objects (VAO) were introduced in OpenGL version 3.0; they
    reduce the amount of function calls that need to be made by storing the set of bindings between vertex attributes
    and vertex data. VAOs are used only if the underlying hardware supports them. This class provides a simple usage pattern
    which is suitable for many applications::

        data = numpy.array([1.3, 5.1, 42.,   0.,
                            3.3, 4.3, 5.1,   1.], dtype=numpy.float32)
        buffer = VertexBuffer(data, [(3, GL_FLOAT), (1, GL_FLOAT)])
        # ... Later when drawing:
        buffer.draw(GL_LINES)
        # Possible setup in a vertex shader:
        # 
        # attribute vec3 position;
        # attribute float index;
        # ...

    What the example above does depends on the rest of the vertex shader (left to your imagination). VertexBuffer constructor
    takes data and data format description as its parameters. Format specifies mapping between data values and vertex attributes.
    See the constructor for more info.
    '''

    def __init__(self, data, format_description, usage=GL_STATIC_DRAW):
        '''
        Constructs VBO and prepares vertex attribute bindings.

        :param data: Data array (vertices) to be sent to the GPU.
        :type numpy.array

        :param format_description: Describes vertex attribute bindings. This parameter must be an iterable
            of tuples. Each tuple specifies a generic vertex attribute (the order is important!) by specifying
            the number of components (must be 1,2,3 or 4) and data type (e.g. GL_FLOAT, GL_INT). See the example
            above. Normalization for fixed-point values is turned off.
        :type an iterable of tuples

        :param usage: Specifies the expected usage pattern. The symbolic constant must be GL_STREAM_DRAW,
            GL_STREAM_READ, GL_STREAM_COPY, GL_STATIC_DRAW, GL_STATIC_READ, GL_STATIC_COPY,
            GL_DYNAMIC_DRAW, GL_DYNAMIC_READ, or GL_DYNAMIC_COPY. Default is GL_STATIC_DRAW.
        :type GLenum 
        '''

        self._format_description = format_description

        if glGenVertexArrays:
            self._vao = GLuint(42)
            glGenVertexArrays(1, self._vao)
            glBindVertexArray(self._vao)
            vertex_buffer_id = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer_id)
            glBufferData(GL_ARRAY_BUFFER, data, usage)

            vertex_size = sum(attribute[0]*4 for attribute in format_description) # TODO: sizeof(type)
            self._num_vertices = len(data) / (vertex_size / 4)
            current_size = 0
            for i, (num_components, type) in enumerate(format_description):
                glVertexAttribPointer(i, num_components, type, GL_FALSE, vertex_size, c_void_p(current_size))
                glEnableVertexAttribArray(i)
                current_size += num_components*4

            glBindVertexArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
        else:
            self._vbo_id = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, self._vbo_id)
            glBufferData(GL_ARRAY_BUFFER, data, usage)
            self._data_length = len(data)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

    def draw(self, primitives=GL_TRIANGLES, first=0, count=-1):
        '''
        Renders primitives from data array. By default it renders triangles using all the data. Consult
        OpenGL documentation (specifically ``glDrawArrays``) for detail info.

        :param primitives: What kind of primitives to render. Symbolic constants GL_POINTS, GL_LINE_STRIP,
            GL_LINE_LOOP, GL_LINES, GL_TRIANGLE_STRIP, GL_TRIANGLE_FAN, GL_TRIANGLES, GL_QUAD_STRIP,
            GL_QUADS, and GL_POLYGON are accepted.
        :type GLenum

        :param first: Specifies the starting index into data.
        :type int

        :param count: The number of indices to be rendered.
        :type int
        '''
        if hasattr(self, '_vao'):
            glBindVertexArray(self._vao)
            glDrawArrays(primitives, first,
                count if count != -1 else self._num_vertices - first)
            glBindVertexArray(0)
        else:
            glBindBuffer(GL_ARRAY_BUFFER, self._vbo_id)

            vertex_size = sum(attribute[0]*4 for attribute in self._format_description)
            current_size = 0
            for i, (num_components, type) in enumerate(self._format_description):
                glVertexAttribPointer(i, num_components, type, GL_FALSE, vertex_size, c_void_p(current_size))
                glEnableVertexAttribArray(i)
                current_size += num_components*4

            glDrawArrays(primitives, first,
                count if count != -1 else self._data_length / (vertex_size / 4) - first)

            for i in range(len(self._format_description)):
                glDisableVertexAttribArray(i)
            glBindBuffer(GL_ARRAY_BUFFER, 0)

class OWOpenGLRenderer:
    '''OpenGL 3 deprecated a lot of old (1.x) functions, particulary, it removed
       immediate mode (glBegin, glEnd, glVertex paradigm). Vertex buffer objects and similar
       (through glDrawArrays for example) should be used instead. This class simplifies
       the usage of that functionality by providing methods which resemble immediate mode.'''

    # TODO: research performance optimizations (maybe store primitives and all of them just once at the end?)

    def __init__(self):
        self._projection = QMatrix4x4()
        self._modelview = QMatrix4x4()

        ## Shader used to draw primitives. Position and color of vertices specified through uniforms. Nothing fancy.
        vertex_shader_source = '''
            attribute float index;
            varying vec4 color;

            uniform vec3 positions[6]; // 6 vertices for quad
            uniform vec4 colors[6];

            uniform mat4 projection;
            uniform mat4 modelview;

            void main(void)
            {
                int i = int(index);
                gl_Position = projection * modelview * vec4(positions[i], 1.);
                color = colors[i];
            }
            '''

        fragment_shader_source = '''
            varying vec4 color;

            void main(void)
            {
                gl_FragColor = color;
            }
            '''

        self._shader = QtOpenGL.QGLShaderProgram()
        self._shader.addShaderFromSourceCode(QtOpenGL.QGLShader.Vertex, vertex_shader_source)
        self._shader.addShaderFromSourceCode(QtOpenGL.QGLShader.Fragment, fragment_shader_source)

        self._shader.bindAttributeLocation('index', 0)

        if not self._shader.link():
            print('Failed to link dummy renderer shader!')

        indices = numpy.array(range(6), dtype=numpy.float32) 
        self._vertex_buffer = VertexBuffer(indices, [(1, GL_FLOAT)])

    def set_transform(self, projection, modelview, viewport=None):
        self._projection = projection
        self._modelview = modelview
        if viewport:
            glViewport(*viewport)
        self._shader.bind()
        self._shader.setUniformValue('projection', projection)
        self._shader.setUniformValue('modelview', modelview)
        self._shader.release()

    def draw_line(self, position0, position1, color0=QColor(0, 0, 0), color1=QColor(0, 0 ,0), color=None):
        '''Draws a line. position0 and position1 must be instances of QVector3D. colors are specified with QColor'''

        if color:
            colors = [color.redF(), color.greenF(), color.blueF(), color.alphaF()] * 2
        else:
            colors = [color0.redF(), color0.greenF(), color0.blueF(), color0.alphaF(),
                      color1.redF(), color1.greenF(), color1.blueF(), color1.alphaF()]

        positions = [position0.x(), position0.y(), position0.z(),
                     position1.x(), position1.y(), position1.z()]

        self._shader.bind()
        glUniform4fv(glGetUniformLocation(self._shader.programId(), 'colors'), len(colors)/4, numpy.array(colors, numpy.float32))
        glUniform3fv(glGetUniformLocation(self._shader.programId(), 'positions'), len(positions)/3, numpy.array(positions, numpy.float32))
        self._vertex_buffer.draw(GL_LINES, 0, 2)
        self._shader.release()

    def draw_rectangle(self, position0, position1, position2, position3,
                       color0=QColor(0, 0, 0), color1=QColor(0, 0, 0), color2=QColor(0, 0, 0), color3=QColor(0, 0, 0), color=None):
        if color:
            colors = [color.redF(), color.greenF(), color.blueF(), color.alphaF()] * 6
        else:
            colors = [color0.redF(), color0.greenF(), color0.blueF(), color0.alphaF(),
                      color1.redF(), color1.greenF(), color1.blueF(), color1.alphaF(),
                      color3.redF(), color3.greenF(), color3.blueF(), color3.alphaF(),

                      color3.redF(), color3.greenF(), color3.blueF(), color3.alphaF(),
                      color1.redF(), color1.greenF(), color1.blueF(), color1.alphaF(),
                      color2.redF(), color2.greenF(), color2.blueF(), color2.alphaF()]

        positions = [position0.x(), position0.y(), position0.z(),
                     position1.x(), position1.y(), position1.z(),
                     position3.x(), position3.y(), position3.z(),

                     position3.x(), position3.y(), position3.z(),
                     position1.x(), position1.y(), position1.z(),
                     position2.x(), position2.y(), position2.z()]

        self._shader.bind()
        glUniform4fv(glGetUniformLocation(self._shader.programId(), 'colors'), len(colors)/4, numpy.array(colors, numpy.float32))
        glUniform3fv(glGetUniformLocation(self._shader.programId(), 'positions'), len(positions)/3, numpy.array(positions, numpy.float32))
        self._vertex_buffer.draw(GL_TRIANGLES, 0, 6)
        self._shader.release()

    def draw_triangle(self, position0, position1, position2,
                       color0=QColor(0, 0, 0), color1=QColor(0, 0, 0), color2=QColor(0, 0, 0), color=None):
        if color:
            colors = [color.redF(), color.greenF(), color.blueF(), color.alphaF()] * 3
        else:
            colors = [color0.redF(), color0.greenF(), color0.blueF(), color0.alphaF(),
                      color1.redF(), color1.greenF(), color1.blueF(), color1.alphaF(),
                      color2.redF(), color2.greenF(), color2.blueF(), color2.alphaF()]

        positions = [position0.x(), position0.y(), position0.z(),
                     position1.x(), position1.y(), position1.z(),
                     position2.x(), position2.y(), position2.z()]

        self._shader.bind()
        glUniform4fv(glGetUniformLocation(self._shader.programId(), 'colors'), len(colors)/4, numpy.array(colors, numpy.float32))
        glUniform3fv(glGetUniformLocation(self._shader.programId(), 'positions'), len(positions)/3, numpy.array(positions, numpy.float32))
        self._vertex_buffer.draw(GL_TRIANGLES, 0, 3)
        self._shader.release()
