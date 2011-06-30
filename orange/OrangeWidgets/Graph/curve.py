
from OWBaseWidget import *
from constants import *
from item import *
import orangegraph

"""
    This class represents a curve on a graph.
    
    .. attribute:: pen_color
    
    .. attribute:: brush_color
        
    .. attribute:: data
        A list of pairs (x,y)
        
    .. attribute:: point_size
        
    .. attribute:: continuous
        If true, the curve is drawn as a continuous line. Otherwise, it's drawn as a series of points
        
    .. method:: symbol(x,y,s=None,parent=None)
        Returns a QGraphicsItem with this curve's symbol at position ``x'',``y'' with size ``s'' and parent ``parent''
        
"""

class Curve(orangegraph.Curve, PlotItem):
    def __init__(self, xData=[], yData=[], x_axis_key=xBottom, y_axis_key=yLeft, parent=None, scene=None):
        orangegraph.Curve.__init__(self, xData, yData, parent, scene)
        PlotItem.__init__(self, xData, yData, x_axis_key, y_axis_key, parent=parent, scene=scene)
        self.set_graph_transform = self.setGraphTransform
        self.setAutoScale(False)
        self._cached_rect = None

    def __setattr__(self, name, value):
        unisetattr(self, name, value, orangegraph.Curve)
        
    
        