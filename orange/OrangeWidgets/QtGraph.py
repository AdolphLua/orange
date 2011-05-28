
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
        self.legend = None
        self.title_item = None
        
        self.canvas = QGraphicsScene(self)
        self.setScene(self.canvas)
        
        self.shown_axes = [xBottom, yLeft]
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
        
        self.palette = palette.shared_palette()
        self.curveSymbols = self.palette.curve_symbols
        self.tips = TooltipManager(self)
        
        self.selectionCurveList = []
        self.curves = []
        self.data_range = {xBottom : (0, 1), yLeft : (0, 1)}
        
        self.map_to_graph = self.map_to_graph_cart
        self.map_from_graph = self.map_from_graph_cart

        self.update()
        
        
    def __setattr__(self, name, value):
        unisetattr(self, name, value, QGraphicsView)
        
    def update(self):
        if self.show_legend and not self.legend:
            self.legend = legend.Legend(self.canvas)
            self.legend.show()
        if not self.show_legend and self.legend:
            self.legend.hide()
            self.legend = None
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
        min_x, max_x = self.data_range[axes[0]]
        min_y, max_y = self.data_range[axes[1]]
        rect = self.graph_area_rect()
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
        if b == self.showXaxisTitle: return
        if b != -1:
            self.showXaxisTitle = b
        if self.showXaxisTitle and self.XaxisTitle:
            self.setAxisTitle(xBottom, self.XaxisTitle)
        else:
            self.setAxisTitle(xBottom, QwtText())
        self.repaint()

    def setXaxisTitle(self, title):
        if title == self.YLaxisTitle: return
        self.XaxisTitle = title
        if self.showXaxisTitle and self.XaxisTitle:
            self.setAxisTitle(xBottom, self.XaxisTitle)
        else:
            self.setAxisTitle(xBottom, QwtText())
        #self.updateLayout()
        self.repaint()

    def setShowYLaxisTitle(self, b = -1):
        if b == self.showYLaxisTitle: return
        if b != -1:
            self.showYLaxisTitle = b
        if self.showYLaxisTitle and self.YLaxisTitle:
            self.setAxisTitle(yLeft, self.YLaxisTitle)
        else:
            self.setAxisTitle(yLeft, QwtText())
        #self.updateLayout()
        self.repaint()

    def setYLaxisTitle(self, title):
        if title == self.YLaxisTitle: return
        self.YLaxisTitle = title
        if self.showYLaxisTitle and self.YLaxisTitle:
            self.setAxisTitle(yLeft, self.YLaxisTitle)
        else:
            self.setAxisTitle(yLeft, QwtText())
        #self.updateLayout()
        self.repaint()

    def setShowYRaxisTitle(self, b = -1):
        if b == self.showYRaxisTitle: return
        if b != -1:
            self.showYRaxisTitle = b
        if self.showYRaxisTitle and self.YRaxisTitle:
            self.setAxisTitle(yRight, self.YRaxisTitle)
        else:
            self.setAxisTitle(yRight, QwtText())
        #self.updateLayout()
        self.repaint()

    def setYRaxisTitle(self, title):
        if title == self.YRaxisTitle: return
        self.YRaxisTitle = title
        if self.showYRaxisTitle and self.YRaxisTitle:
            self.setAxisTitle(yRight, self.YRaxisTitle)
        else:
            self.setAxisTitle(yRight, QwtText())
        #self.updateLayout()
        self.repaint()

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
        pass
        
    def setAxisTitle(self, axis_id, title):
        self.axes[axis_id].set_title(title)
        pass
        
    def setTickLength(self, axis_id, minor, medium, major):
        self.axes[axis_id].set_tick_legth(minor, medium, major)
        pass

    def setYLlabels(self, labels):
        pass
    def setYRlabels(self, labels):
        pass
        
    def addCurve(self, name, brushColor = Qt.black, penColor = Qt.black, size = 5, style = Qt.SolidLine, 
                 symbol = palette.EllipseShape, enableLegend = 0, xData = [], yData = [], showFilledSymbols = None,
                 lineWidth = 1, pen = None, autoScale = 0, antiAlias = None, penAlpha = 255, brushAlpha = 255):
        self.data_range[xBottom] = ( min(xData), max(xData) )
        self.data_range[yLeft] = ( min(yData), max(yData) )
        data = []
        for i in range(len(xData)):
            data.append( (xData[i], yData[i]) )
            c = curve.Curve(data, self.palette.line_styles[0], self)
            c.setPos(self.graph_area.bottomLeft())
            self.canvas.addItem(c)
            self.curves.append(c)
        return c
        
    def addAxis(self, axis_id, line, text):
        pass        
    
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
        if xBottom in self.shown_axes:
            bottom_rect = QRectF(graph_rect)
            bottom_rect.setTop( bottom_rect.bottom() - margin)
            axis_rects[xBottom] = bottom_rect
            graph_rect.setBottom( graph_rect.bottom() - margin)
        if xTop in self.shown_axes:
            top_rect = QRectF(graph_rect)
            top_rect.setBottom(top_rect.top() + margin)
            axis_rects[xTop] = top_rect
            graph_rect.setTop(graph_rect.top() + margin)
        if yLeft in self.shown_axes:
            left_rect = QRectF(graph_rect)
            left = graph_rect.left() + margin
            left_rect.setRight(left)
            graph_rect.setLeft(left)
            axis_rects[yLeft] = left_rect
            if xBottom in axis_rects:
                axis_rects[xBottom].setLeft(left)
            if xTop in axis_rects:
                axis_rects[xTop].setLeft(left)
        if yRight in self.shown_axes:
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
            
        self.axes = dict()
            
        for id, rect in axis_rects.iteritems():
            if id is xBottom:
                line = QLineF(rect.topLeft(),  rect.topRight())
            elif id is xTop:
                line = QLineF(rect.bottomLeft(), rect.bottomRight())
            elif id is yLeft:
                line = QLineF(rect.bottomRight(), rect.topRight())
            elif id is yRight:
                line = QLineF(rect.bottomRight(), rect.topRight())
            line.translate(-rect.topLeft())
            self.axes[id] = axis.Axis(rect.size(), 'Test', line )
            self.axes[id].setPos(rect.topLeft())
            self.canvas.addItem(self.axes[id])
            
        for c in self.curves:
            c.update()
        self.setSceneRect(self.canvas.itemsBoundingRect())
