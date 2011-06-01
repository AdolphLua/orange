
"""
    .. class:: QtGraph
        The base class for all graphs in Orange. It is written in Qt with QGraphicsItems
        
    .. attribute:: show_legend
        A boolean controlling whether the legend is displayed or not
        
    .. attribute:: legend_position
        Determines where the legend is positions, if ``show_legend`` is True.
        
    .. atribute:: palette
        Chooses which palette is used by this graph. By default, this is `shared_palette`. 
        
    .. method map_to_graph(axis_ids, point)
        Maps the ``point`` in data coordinates to graph (scene) coordinates
        This method has to be reimplemented in graphs with special axes (RadViz, PolyViz)
        
    .. method map_from_graph(axis_ids, point)
        Maps the ``point`` from scene coordinates to data coordinates
        This method has to be reimplemented in graphs with special axes (RadViz, PolyViz)
        
    .. method activateZooming()
        Activates zoom
        
    .. method clear()
        Removes all curves from the graph
        
    .. method graph_area_rect()
        Return the QRectF of the area where data is plotted (without axes)
"""

NOTHING = 0
ZOOMING = 1
SELECT_RECTANGLE = 2
SELECT_POLYGON = 3
PANNING = 4
SELECT = 5

yLeft = 0
yRight = 1
xBottom = 2
xTop = 3
axisCnt = 4

LeftLegend = 0
RightLegend = 1
BottomLegend = 2
TopLegend = 3
ExternalLegend = 4

from Graph import *
from PyQt4.QtGui import QGraphicsView,  QGraphicsScene

from OWDlgs import OWChooseImageSizeDlg
from OWBaseWidget import unisetattr
from OWGraphTools import *      # user defined curves, ...

class OWGraph(QGraphicsView):
    def __init__(self, parent=None,  name="None",  show_legend=1 ):
        QGraphicsView.__init__(self, parent)
        self.parent_name = name
        self.show_legend = show_legend
        self._legend = None
        self.title_item = None
        
        self.canvas = QGraphicsScene(self)
        self.setScene(self.canvas)
        
        self.axes = dict()
        self.axis_margin = 150
        self.title_margin = 100
        self.showMainTitle = True
        self.mainTitle = "Qt Graph"
        self.XaxisTitle = None
        self.YLaxisTitle = None
        self.YRaxisTitle = None
        
        # Method aliases, because there are some methods with different names but same functions
        self.repaint = self.update
        self.setCanvasBackground = self.setCanvasColor
        
        # OWScatterPlot needs these:
        self.alphaValue = 1
        self.useAntialiasing = False
        
        self.palette = palette.shared_palette()
        self.curveSymbols = self.palette.curve_symbols
        self.tips = TooltipManager(self)
        
        self.selectionCurveList = []
        self.curves = []
        self.data_range = {xBottom : (0, 1), yLeft : (0, 1)}
        self.addAxis(xBottom, False)
        self.addAxis(yLeft, True)
        
        self.map_to_graph = self.map_to_graph_cart
        self.map_from_graph = self.map_from_graph_cart
        
        ## Performance optimization
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self.update()
        
        
    def __setattr__(self, name, value):
        unisetattr(self, name, value, QGraphicsView)
        
    def update(self):
        if self.show_legend and not self._legend:
            self._legend = legend.Legend(self.canvas)
            self._legend.show()
        if not self.show_legend and self._legend:
            self._legend.hide()
            self._legend = None
        self.replot()
            
    def graph_area_rect(self):
        """
        rect = self.childrenRect()
        if xBottom in self.axes:
            rect.setBottom(rect.bottom() - self.axis_margin)
        if yLeft in self.axes:
            rect.setLeft(rect.left() + self.axis_margin)
        return rect
        """
        return self.graph_area
        
    def map_to_graph_cart(self, point, axes=None):
        px, py = point
        if not axes:
            axes = [xBottom, yLeft]
        min_x, max_x, t = self.axes[axes[0]].scale
        min_y, max_y, t = self.axes[axes[1]].scale
        rect = self.graph_area
        rx = (px - min_x) * rect.width() / (max_x - min_x)
        ry = -(py - min_y) * rect.height() / (max_y - min_y)
        return (rx, ry)
        
    def map_from_graph_cart(self, point, axes = None):
        px, py = point
        if not axes:
            axes = [xBottom, yLeft]
        min_x, max_x = self.data_range[axes[0]]
        min_y, max_y = self.data_range[axes[1]]
        rect = self.graph_area_rect()
        rx = (px - rect.left()) / rect().width() * (max_x - min_x)
        ry = -(py - rect.bottom()) / rect.height() * (max_y - min_y)
        return (rx, ry)
        
    def saveToFile(self, extraButtons = []):
        sizeDlg = OWChooseImageSizeDlg(self, extraButtons, parent=self)
        sizeDlg.exec_()

    def saveToFileDirect(self, fileName, size = None):
        sizeDlg = OWChooseImageSizeDlg(self)
        sizeDlg.saveImage(fileName, size)
        
    def activateZooming(self):
        self.state = ZOOMING
        
    def setShowMainTitle(self, b):
        self.showMainTitle = b
        if self.showMainTitle and self.mainTitle:
            self.setTitle(self.mainTitle)
        else:
            self.setTitle('')
        self.repaint()

    def setMainTitle(self, t):
        self.mainTitle = t
        if self.showMainTitle and self.mainTitle:
            self.setTitle(self.mainTitle)
        else:
            self.setTitle('')
        self.repaint()

    def setShowXaxisTitle(self, b = -1):
        self.setShowAxisTitle(xBottom, b)
        
    def setXaxisTitle(self, title):
        self.setAxisTitle(xBottom, title)

    def setShowYLaxisTitle(self, b = -1):
        self.setShowAxisTitle(yLeft, b)

    def setYLaxisTitle(self, title):
        self.setAxisTitle(yLeft, title)

    def setShowYRaxisTitle(self, b = -1):
        self.setShowAxisTitle(yRight, b)

    def setYRaxisTitle(self, title):
        self.setAxisTitle(yRight, title)

    def enableGridXB(self, b):
      #  self.gridCurve.enableX(b)
        self.replot()

    def enableGridYL(self, b):
       # self.gridCurve.enableY(b)
        self.replot()

    def setGridColor(self, c):
       # self.gridCurve.setPen(QPen(c))
        self.replot()

    def setCanvasColor(self, c):
        self.canvas.setBackgroundBrush(c)
        
    def setData(self, data):
        # clear all curves, markers, tips
        # self.clear()
        # self.removeAllSelections(0)  # clear all selections
        # self.tips.removeAll()
        self.zoomStack = []
        self.replot()
        
    def setXlabels(self, labels):
        if xBottom in self.axes:
            self.setAxisLabels(xBottom, labels)
        elif xTop in self.axes:
            self.setAxisLabels(xTop, labels)
        
    def setAxisLabels(self, axis_id, labels):
        self.axes[axis_id].set_labels(labels)
    
    def setAxisScale(self, axis_id, min, max, step_size=0):
        self.axes[axis_id].set_scale(min, max, step_size)
        
    def setAxisTitle(self, axis_id, title):
        if axis_id in self.axes:
            self.axes[axis_id].set_title(title)
            
    def setShowAxisTitle(self, axis_id, b):
        if axis_id in self.axes:
            self.axes[axis_id].set_show_title(b)
        
    def setTickLength(self, axis_id, minor, medium, major):
        if axis_id in self.axes:
            self.axes[axis_id].set_tick_legth(minor, medium, major)

    def setYLlabels(self, labels):
        self.setAxisLabels(yLeft, labels)

    def setYRlabels(self, labels):
        self.setAxisLabels(yRight, labels)
        
    def addCurve(self, name, brushColor = Qt.black, penColor = Qt.black, size = 5, style = Qt.NoPen, 
                 symbol = palette.EllipseShape, enableLegend = 0, xData = [], yData = [], showFilledSymbols = None,
                 lineWidth = 1, pen = None, autoScale = 0, antiAlias = None, penAlpha = 255, brushAlpha = 255):
        data = []
        for i in range(len(xData)):
            data.append( (xData[i], yData[i]) )
        c = curve.Curve(data, self.palette.line_style(len(self.curves)), self)
        c.setPos(self.graph_area.bottomLeft())
        c.continuous = (style is not Qt.NoPen)
        c.update()
        self.canvas.addItem(c)
        self.curves.append(c)
        return c
        
    def addAxis(self, axis_id, title_above = False):
        self.axes[axis_id] = axis.Axis(title_above)
    
    def removeAllSelections(self):
        pass
        
    def clear(self):
        for c in self.curves:
            self.canvas.removeItem(c)
        del self.curves[:]
        
    def replot(self):
        graph_rect = QRectF(self.childrenRect())
        
        if self.showMainTitle and self.mainTitle:
            if self.title_item:
                self.canvas.removeItem(self.title_item)
                del self.title_item
            self.title_item = QGraphicsTextItem(self.mainTitle)
            title_size = self.title_item.boundingRect().size()
            ## TODO: Check if the title is too big
            self.title_item.setPos( graph_rect.width()/2 - title_size.width()/2, self.title_margin/2 - title_size.height()/2 )
            self.canvas.addItem(self.title_item)
            graph_rect.setTop(graph_rect.top() + self.title_margin)
        
        axis_rects = dict()
        margin = min(self.axis_margin,  graph_rect.height()/4, graph_rect.height()/4)
        margin = 40
        if xBottom in self.axes and self.axes[xBottom].isVisible():
            bottom_rect = QRectF(graph_rect)
            bottom_rect.setTop( bottom_rect.bottom() - margin)
            axis_rects[xBottom] = bottom_rect
            graph_rect.setBottom( graph_rect.bottom() - margin)
        if xTop in self.axes and self.axes[xTop].isVisible():
            top_rect = QRectF(graph_rect)
            top_rect.setBottom(top_rect.top() + margin)
            axis_rects[xTop] = top_rect
            graph_rect.setTop(graph_rect.top() + margin)
        if yLeft in self.axes and self.axes[yLeft].isVisible():
            left_rect = QRectF(graph_rect)
            left = graph_rect.left() + margin
            left_rect.setRight(left)
            graph_rect.setLeft(left)
            axis_rects[yLeft] = left_rect
            if xBottom in axis_rects:
                axis_rects[xBottom].setLeft(left)
            if xTop in axis_rects:
                axis_rects[xTop].setLeft(left)
        if yRight in self.axes and self.axes[yRight].isVisible():
            right_rect = QRectF(graph_rect)
            right = graph_rect.right() - margin
            right_rect.setLeft(right)
            graph_rect.setRight(right)
            axis_rects[yRight] = right_rect
            if xBottom in axis_rects:
                axis_rects[xBottom].setRight(right)
            if xTop in axis_rects:
                axis_rects[xTop].setRight(right)
                
        self.graph_area = graph_rect
        
        for id, item in self.axes.iteritems():
            self.canvas.removeItem(item)
            
        for id, rect in axis_rects.iteritems():
            if id is xBottom:
                line = QLineF(rect.topLeft(),  rect.topRight())
            elif id is xTop:
                line = QLineF(rect.bottomLeft(), rect.bottomRight())
            elif id is yLeft:
                line = QLineF(rect.bottomRight(), rect.topRight())
            elif id is yRight:
                line = QLineF(rect.bottomLeft(), rect.topLeft())
            line.translate(-rect.topLeft())
            a = self.axes[id]
            a.set_size(rect.size())
            a.set_line(line)
            a.setPos(rect.topLeft())
            self.canvas.addItem(a)
            a.update()
            a.show()
            
        for c in self.curves:
            c.setPos(self.graph_area.bottomLeft())
            c.update()
        self.setSceneRect(self.canvas.itemsBoundingRect())
        
    def legend(self):
        return self._legend
        
    ## Event handling
    def resizeEvent(self, event):
        self.replot()
