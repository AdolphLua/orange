"""
    .. class:: OWPlot
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
        
    .. method send_data():
        This method is not defined here, it is up to subclasses to implement it. 
        It should send selected examples to the next widget
        
    .. method add_curve(name, attributes, ...)
        Attributes is a map of { point_property: ("data_property", value) }, for example 
            { PointColor : ("building_type", "house"), PointSize : ("age", 20) }
"""

NOTHING = 0
ZOOMING = 1
SELECT_RECTANGLE = 2
SELECT_POLYGON = 3
PANNING = 4
SELECT = 5

LeftLegend = 0
RightLegend = 1
BottomLegend = 2
TopLegend = 3
ExternalLegend = 4

from owaxis import *
from owcurve import *
from owlegend import *
from owpalette import *
from owtools import *


from PyQt4.QtGui import QGraphicsView,  QGraphicsScene, QPainter, QTransform, QPolygonF, QGraphicsItem, QGraphicsPolygonItem, QGraphicsRectItem, QRegion
from PyQt4.QtCore import QPointF, QPropertyAnimation, pyqtProperty

from OWDlgs import OWChooseImageSizeDlg
from OWBaseWidget import unisetattr
from OWColorPalette import *      # color palletes, ...
from Orange.misc import deprecated_members, deprecated_attribute

import orangeplot

def n_min(*args):
    lst = args[0] if len(args) == 1 else args
    a = [i for i in lst if i is not None]
    return min(a) if a else None
    
def n_max(*args):
    lst = args[0] if len(args) == 1 else args
    a = [i for i in lst if i is not None]
    return max(a) if a else None
    
name_map = {
    "saveToFileDirect": "save_to_file_direct",  
    "saveToFile" : "save_to_file", 
    "addCurve" : "add_curve", 
    "addMarker" : "add_marker", 
    "updateLayout" : "update_layout", 
    "activateZooming" : "activate_zooming", 
    "activateRectangleSelection" : "activate_rectangle_selection", 
    "activatePolygonSelection" : "activate_polygon_selection", 
    "getSelectedPoints" : "get_selected_points",
    "setAxisScale" : "set_axis_scale",
    "setAxisLabels" : "set_axis_labels", 
    "setTickLength" : "set_axis_tick_length"
}

@deprecated_members(name_map, wrap_methods=name_map.keys())
class OWPlot(orangeplot.Plot):
    def __init__(self, parent = None,  name = "None",  show_legend = 1, axes = [xBottom, yLeft] ):
        orangeplot.Plot.__init__(self, parent)
        self.parent_name = name
        self.show_legend = show_legend
        self.title_item = None
        
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
     #   self.graph_item.setPen(QPen(Qt.NoPen))
        
        self._legend = OWLegend(self.scene())
        self.axes = dict()
        self.axis_margin = 80
        self.title_margin = 50
        self.graph_margin = 30
        self.mainTitle = None
        self.showMainTitle = False
        self.XaxisTitle = None
        self.YLaxisTitle = None
        self.YRaxisTitle = None
                
        # Method aliases, because there are some methods with different names but same functions
        self.setCanvasBackground = self.setCanvasColor
        
        # OWScatterPlot needs these:
        self.alphaValue = 1
        self.useAntialiasing = True
        
        self.palette = shared_palette()
        self.curveSymbols = self.palette.curve_symbols
        self.tips = TooltipManager(self)
        
        self.state = NOTHING
        self._pressed_mouse_button = Qt.NoButton
        self.selection_items = []
        self._current_rs_item = None
        self._current_ps_item = None
        self.polygon_close_treshold = 10
        self.sendSelectionOnUpdate = False
        self.auto_send_selection_callback = None
        
        self.data_range = {}
        self.map_transform = QTransform()
        self.graph_area = QRectF()
        
        ## Performance optimization
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setInteractive(False)
        
        self._bounds_cache = {}
        self._transform_cache = {}
        self.block_update = False
        
        ## Mouse event handlers
        self.mousePressEventHandler = None
        self.mouseMoveEventHandler = None
        self.mouseReleaseEventHandler = None
        self.mouseStaticClickHandler = self.mouseStaticClick
        
        self._marker_items = []
        
        self._zoom_factor = 1
        self._zoom_point = None
        self.zoom_transform = QTransform()
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        ## Add specified axes:
        
        for key in axes:
            if key in [yLeft, xTop]:
                self.add_axis(key, title_above=1)
            else:
                self.add_axis(key)
                
        self.contPalette = ColorPaletteGenerator(numberOfColors = -1)
        self.discPalette = ColorPaletteGenerator()

        self.replot()
        
        
    selectionCurveList = deprecated_attribute("selectionCurveList", "selection_items")
    autoSendSelectionCallback = deprecated_attribute("autoSendSelectionCallback", "auto_send_selection_callback")
    
    def __setattr__(self, name, value):
        unisetattr(self, name, value, QGraphicsView)
        
    def scrollContentsBy(self, dx, dy):
        # This is overriden here to prevent scrolling with mouse and keyboard
        # Instead of moving the contents, we simply do nothing
        pass
    
    def graph_area_rect(self):
        return self.graph_area
        
    def map_to_graph(self, point, axes = None):
        (x, y) = point
        ret = QPointF(x, y) * self.map_transform
        return (ret.x(), ret.y())
        
    def map_from_graph(self, point, axes = None):
        (x, y) = point
        ret = QPointF(x, y) * self.map_transform.inverted()
        return (ret.x(), ret.y())
        
    def save_to_file(self, extraButtons = []):
        sizeDlg = OWChooseImageSizeDlg(self, extraButtons, parent=self)
        sizeDlg.exec_()
        
    def save_to_file_direct(self, fileName, size = None):
        sizeDlg = OWChooseImageSizeDlg(self)
        sizeDlg.saveImage(fileName, size)
        
    def activate_zooming(self):
        self.state = ZOOMING
        
    def activate_rectangle_selection(self):
        self.state = SELECT_RECTANGLE
        
    def activate_polygon_selection(self):
        self.state = SELECT_POLYGON
        
    def setShowMainTitle(self, b):
        self.showMainTitle = b
        self.replot()

    def setMainTitle(self, t):
        self.mainTitle = t
        self.replot()

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
        self.scene().setBackgroundBrush(c)
        
    def setData(self, data):
        self.clear()
        self.zoomStack = []
        self.replot()
        
    def setXlabels(self, labels):
        if xBottom in self.axes:
            self.set_axis_labels(xBottom, labels)
        elif xTop in self.axes:
            self.set_axis_labels(xTop, labels)
        
    def set_axis_labels(self, axis_id, labels):
        if axis_id in self._bounds_cache:
            del self._bounds_cache[axis_id]
        self._transform_cache = {}
        self.axes[axis_id].set_labels(labels)
    
    def set_axis_scale(self, axis_id, min, max, step_size=0):
        qDebug('Setting axis scale for ' + str(axis_id) + ' with axes ' + ' '.join(str(i) for i in self.axes))
        if axis_id in self._bounds_cache:
            del self._bounds_cache[axis_id]
        self._transform_cache = {}
        self.axes[axis_id].set_scale(min, max, step_size)
        
    def setAxisTitle(self, axis_id, title):
        if axis_id in self.axes:
            self.axes[axis_id].set_title(title)
            
    def setShowAxisTitle(self, axis_id, b):
        if axis_id in self.axes:
            self.axes[axis_id].set_show_title(b)
        
    def set_axis_tick_length(self, axis_id, minor, medium, major):
        if axis_id in self.axes:
            self.axes[axis_id].set_tick_legth(minor, medium, major)

    def setYLlabels(self, labels):
        self.set_axis_labels(yLeft, labels)

    def setYRlabels(self, labels):
        self.set_axis_labels(yRight, labels)
        
    def add_custom_curve(self, curve, enableLegend = False):
        self.addItem(curve)
        if enableLegend:
            self.legend().add_curve(curve)
        for key in [curve.axes()]:
            if key in self._bounds_cache:
                del self._bounds_cache[key]
        self._transform_cache = {}
        if hasattr(curve, 'tooltip'):
            curve.setToolTip(curve.tooltip)
        return curve
        
    def add_curve(self, name, brushColor = Qt.black, penColor = Qt.black, size = 5, style = Qt.NoPen, 
                 symbol = OWCurve.Ellipse, enableLegend = False, xData = [], yData = [], showFilledSymbols = None,
                 lineWidth = 1, pen = None, autoScale = 0, antiAlias = None, penAlpha = 255, brushAlpha = 255, 
                 x_axis_key = xBottom, y_axis_key = yLeft):
        
        c = OWCurve(xData, yData, parent=self.graph_item)
        c.setAxes(x_axis_key, y_axis_key)
        c.setToolTip(name)
        c.name = name
        c.setAutoUpdate(False)
        c.setContinuous(style is not Qt.NoPen)
        c.setColor(brushColor)
        c.setSymbol(symbol)
        c.setPointSize(size)
        c.setData(xData,  yData)
        c.setGraphTransform(self.transform_for_axes(x_axis_key, y_axis_key))
        
        c.setAutoScale(autoScale)
        
        return self.add_custom_curve(c, enableLegend)
        
    def remove_curve(self, item):
        self.removeItem(item)
        self.legend().remove_curve(item)
        
    def plot_data(self, xData, yData, colors, labels, shapes, sizes):
        pass
        
    def add_axis(self, axis_id, title = '', title_above = False, title_location = AxisMiddle, line = None, arrows = NoPosition, zoomable = False):
        qDebug('Adding axis with id ' + str(axis_id) + ' and title ' + title)
        a = OWAxis(axis_id, title, title_above, title_location, line, arrows, scene=self.scene())
        a.zoomable = zoomable
        a.update_callback = self.replot
        if axis_id in self._bounds_cache:
            del self._bounds_cache[axis_id]
        self._transform_cache = {}
        self.axes[axis_id] = a
        
    def remove_all_axes(self, user_only = True):
        ids = []
        for id,item in self.axes.iteritems():
            if not user_only or id >= UserAxis:
                ids.append(id)
                self.scene().removeItem(item)
        for id in ids:
            del self.axes[id]
        
    def add_custom_axis(self, axis_id, axis):
        self.axes[axis_id] = axis
        
    def add_marker(self, name, x, y, alignment = -1, bold = 0, color = None, brushColor = None, size=None, antiAlias = None, 
                    x_axis_key = xBottom, y_axis_key = yLeft):
        text = name
        if bold:
            text = '<b>' + text + '</b>'
        item = QGraphicsTextItem(parent=self.graph_item, scene=self.scene())
        item.setHtml(text)
        (dx,dy) = (4,4)
        (px,py) = self.map_to_graph((x,y))
        item.setPos(px+dx,py+dy)
        if color:
            item.setPen(QPen(color))
        if brushColor:
            item.setBrush(QBrush(brushColor))
            
        self._marker_items.append((item, x, y, x_axis_key, y_axis_key))
        
    def removeAllSelections(self):
        ## TODO
        pass
        
    def clear(self):
        for i in self.itemList():
            self.removeItem(i)
        self._bounds_cache = {}
        self._transform_cache = {}
        self.clear_markers()
        self.legend().clear()
        
    def clear_markers(self):
        for item,x,y,x_axis,y_axis in self._marker_items:
            self.scene().removeItem(item)
        self._marker_items = []
        
    def update_layout(self):
        graph_rect = QRectF(self.contentsRect())
        self.centerOn(graph_rect.center())
        m = self.graph_margin
        graph_rect.adjust(m, m, -m, -m)
        
        if self.showMainTitle and self.mainTitle:
            if self.title_item:
                self.scene().removeItem(self.title_item)
                del self.title_item
            self.title_item = QGraphicsTextItem(self.mainTitle, scene=self.scene())
            title_size = self.title_item.boundingRect().size()
            ## TODO: Check if the title is too big
            self.title_item.setPos( graph_rect.width()/2 - title_size.width()/2, self.title_margin/2 - title_size.height()/2 )
            graph_rect.setTop(graph_rect.top() + self.title_margin)
        
        if self.show_legend:
            ## TODO: Figure out a good placement for the legend, possibly outside the graph area
            self._legend.setPos(graph_rect.topRight() - QPointF(100, 0))
            self._legend.show()
        else:
            self._legend.hide()
        
        axis_rects = dict()
        margin = min(self.axis_margin,  graph_rect.height()/4, graph_rect.height()/4)
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
                
        if self.graph_area != graph_rect:
            self.graph_area = QRectF(graph_rect)
            self.setGraphRect(self.graph_area)
            self._transform_cache = {}
            self.map_transform = self.transform_for_axes()
        
        for c in self.itemList():
            x,y = c.axes()
            c.setGraphTransform(self.transform_for_axes(x,y))
            c.updateProperties()
            
    def update_zoom(self):
      #  self.setViewportUpdateMode(QGraphicsView.NoViewportUpdate)
        self.zoom_transform = self.transform_for_zoom(self._zoom_factor, self._zoom_point, self.graph_area)
        self.zoom_rect = self.zoom_transform.mapRect(self.graph_area)
        for c in self.itemList():
            c.set_zoom_factor(self._zoom_factor)
            c.updateProperties()
        self.graph_item.setTransform(self.zoom_transform)
        for a in self.axes.values():
            if a.zoomable:
                a.zoom_transform = self.zoom_transform
                a.update()
            
        for item, region in self.selection_items:
            item.setTransform(self.zoom_transform)
            
        for item,x,y,x_axis,y_axis in self._marker_items:
            p = QPointF(x,y) * self.transform_for_axes(x_axis, y_axis) * self.zoom_transform + QPointF(4,4)
            r = item.boundingRect()
            item.setPos(p - r.center() + r.topLeft())
            
        self.update_axes()
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.update()
        
    def update_axes(self):
        for id, item in self.axes.iteritems():
            if item.scale is None and item.labels is None:
                item.auto_range = self.bounds_for_axis(id)
            
            if id in XAxes:
                (x,y) = (id, yLeft)
            elif id in YAxes:
                (x,y) = (xBottom, id)
            else:
                (x,y) = (xBottom, yLeft)
                
            if id in CartesianAxes:
                ## This class only sets the lines for these four axes, widgets are responsible for the rest
                if x in self.axes and y in self.axes:
                    rect = self.data_rect_for_axes(x,y)
                    if id == xBottom:
                        line = QLineF(rect.topLeft(), rect.topRight())
                    elif id == xTop:
                        line = QLineF(rect.bottomLeft(), rect.bottomRight())
                    elif id == yLeft:
                        line = QLineF(rect.topLeft(), rect.bottomLeft())
                    elif id == yRight:
                        line = QLineF(rect.topRight(), rect.bottomRight())
                    else:
                        line = None
                    item.data_line = line
            if item.data_line:
                t = self.transform_for_axes(x, y)
                graph_line = t.map(item.data_line)
                if item.zoomable:
                    item.graph_line = self.zoom_transform.map(graph_line)
                else:
                    item.graph_line = graph_line
                item.graph_line.translate(self.graph_item.pos())
            item.update()
        
    def replot(self, force = False):
        if not self.block_update or force:
            if self.isDirty():
                qDebug('Graph is dirty, clearing caches')
                self._bounds_cache = {}
                self._transform_cache = {}
                self.setClean()
            self.update_layout()
            self.update_zoom()
            self.update_axes()
            self.update()
            ## TODO: fitInView is very slow, but resetTransform doesn't seem to be doing its job
            self.resetTransform()
            # self.fitInView(QRectF(self.contentsRect()))
            
    def legend(self):
        return self._legend
        
    ## Event handling
    def resizeEvent(self, event):
        self.replot()
        
    def mousePressEvent(self, event):
        if self.mousePressEventHandler and self.mousePressEventHandler(event):
            event.accept()
            return
        self.static_click = True
        self._pressed_mouse_button = event.button()
        point = self.map_from_widget(event.pos())
        if event.button() == Qt.LeftButton and self.state == SELECT_RECTANGLE and self.graph_area.contains(point):
            self._selection_start_point = self.map_from_widget(event.pos())
            self._current_rs_item = QGraphicsRectItem(parent=self.graph_item, scene=self.scene())
            
    def mouseMoveEvent(self, event):
        if self.mouseMoveEventHandler and self.mouseMoveEventHandler(event):
            event.accept()
            return
        if event.buttons():
            self.static_click = False
        point = self.map_from_widget(event.pos())
        if self._pressed_mouse_button == Qt.LeftButton:
            if self.state == SELECT_RECTANGLE and self._current_rs_item and self.graph_area.contains(point):
                self._current_rs_item.setRect(QRectF(self._selection_start_point, point).normalized())
        if not self._pressed_mouse_button and self.state == SELECT_POLYGON and self._current_ps_item:
            self._current_ps_polygon[-1] = point
            self._current_ps_item.setPolygon(self._current_ps_polygon)
            if self._current_ps_polygon.size() > 2 and self.points_equal(self._current_ps_polygon.first(), self._current_ps_polygon.last()):
                highlight_pen = QPen()
                highlight_pen.setWidth(2)
                highlight_pen.setStyle(Qt.DashDotLine)
                self._current_ps_item.setPen(highlight_pen)
            else:
                self._current_ps_item.setPen(QPen(Qt.black))
            
    def mouseReleaseEvent(self, event):
        if self.mouseReleaseEventHandler and self.mouseReleaseEventHandler(event):
            event.accept()
            return
        if self.static_click and self.mouseStaticClickHandler and self.mouseStaticClickHandler(event):
            event.accept()
            return
        self._pressed_mouse_button = Qt.NoButton
        if event.button() == Qt.LeftButton and self.state == SELECT_RECTANGLE and self._current_rs_item:
            self.add_selection_item(self._current_rs_item, self._current_rs_item.rect())
            self._current_rs_item = None
    
    def mouseStaticClick(self, event):
        point = self.map_from_widget(event.pos())
        if self.state == ZOOMING:
            t, ok = self.zoom_transform.inverted()
            if not ok:
                return False
            p = point * t
            if event.button() == Qt.LeftButton:
                end_zoom_factor = self._zoom_factor * 2
                self._zoom_point = p
            elif event.button() == Qt.RightButton:
                end_zoom_factor = max(self._zoom_factor/2, 1)
            else:
                return False
            self.zoom_factor_animation = QPropertyAnimation(self, 'zoom_factor')
            self.zoom_factor_animation.setStartValue(float(self._zoom_factor))
            self.zoom_factor_animation.setEndValue(float(end_zoom_factor))
            self.zoom_factor_animation.start(QPropertyAnimation.DeleteWhenStopped)
            return True
            
        elif self.state == SELECT_POLYGON and event.button() == Qt.LeftButton:
            if not self._current_ps_item:
                self._current_ps_polygon = QPolygonF()
                self._current_ps_polygon.append(point)
                self._current_ps_item = QGraphicsPolygonItem(self.graph_item, self.scene())
            self._current_ps_polygon.append(point)
            self._current_ps_item.setPolygon(self._current_ps_polygon)
            if self._current_ps_polygon.size() > 2 and self.points_equal(self._current_ps_polygon.first(), self._current_ps_polygon.last()):
                self._current_ps_item.setPen(QPen(Qt.black))
                self._current_ps_polygon.append(self._current_ps_polygon.first())
                self.add_selection_item(self._current_ps_item, self._current_ps_polygon)
                self._current_ps_item = None
                
        elif self.state in [SELECT_RECTANGLE, SELECT_POLYGON] and event.button() == Qt.RightButton:
            qDebug('Right conditions for removing a selection curve ' + repr(self.selection_items))
            self.selection_items.reverse()
            for item, region in self.selection_items:
                qDebug(repr(point) + '   ' + repr(region.rects()))
                if region.contains(point.toPoint()):
                    self.scene().removeItem(item)
                    qDebug('Removed a selection curve')
                    self.selection_items.remove((item, region))
                    if self.auto_send_selection_callback: 
                        self.auto_send_selection_callback()
                    break
            self.selection_items.reverse()
        else:
            return False
            
    @staticmethod
    def transform_from_rects(r1, r2):
        if r1.width() == 0 or r1.height() == 0 or r2.width() == 0 or r2.height() == 0:
            return QTransform()
        tr1 = QTransform().translate(-r1.left(), -r1.top())
        ts = QTransform().scale(r2.width()/r1.width(), r2.height()/r1.height())
        tr2 = QTransform().translate(r2.left(), r2.top())
        return tr1 * ts * tr2
        
    def transform_for_zoom(self, factor, point, rect):
        if factor == 1:
            return QTransform()
            
        dp = point
        
        t = QTransform()
        t.translate(dp.x(), dp.y())
        t.scale(factor, factor)
        t.translate(-dp.x(), -dp.y())
        return t

    @pyqtProperty(QRectF)
    def zoom_area(self):
        return self._zoom_area
        
    @zoom_area.setter
    def zoom_area(self, value):
        self._zoom_area = value
        self.zoom_transform = self.transform_from_rects(self._zoom_area, self.graph_area)
        self.zoom_rect = self.zoom_transform.mapRect(self.graph_area)
        self.replot()
        
    @pyqtProperty(float)
    def zoom_factor(self):
        return self._zoom_factor
        
    @zoom_factor.setter
    def zoom_factor(self, value):
        self._zoom_factor = value
        self.update_zoom()
        
    @pyqtProperty(QPointF)
    def zoom_point(self):
        return self._zoom_point
        
    @zoom_point.setter
    def zoom_point(self, value):
        self._zoom_point = value
        self.update_zoom()
        
    def set_state(self, state):
        self.state = state
        if state != SELECT_RECTANGLE:
            self._current_rs_item = None
        if state != SELECT_POLYGON:
            self._current_ps_item = None
        
    def map_from_widget(self, point):
        return self.mapToScene(point) - self.graph_item.pos()
        
    def get_selected_points(self, xData, yData, validData):
        region = QRegion()
        selected = []
        unselected = []
        for item, reg in self.selection_items:
            region |= reg
        for j in range(len(xData)):
            (x, y) = self.map_to_graph( (xData[j], yData[j]) )
            p = (QPointF(xData[j], yData[j]) * self.map_transform).toPoint()
            sel = region.contains(p)
            selected.append(sel)
            unselected.append(not sel)
        return selected, unselected
        
    def add_selection_item(self, item, reg):
        if type(reg) == QRectF:
            reg = reg.toRect()
        elif type(reg) == QPolygonF:
            reg = reg.toPolygon()
        t = (item, QRegion(reg))
        self.selection_items.append(t)
        if self.auto_send_selection_callback:
            self.auto_send_selection_callback()
        
    def points_equal(self, p1, p2):
        if type(p1) == tuple:
            (x, y) = p1
            p1 = QPointF(x, y)
        if type(p2) == tuple:
            (x, y) = p2
            p2 = QPointF(x, y)
        return (QPointF(p1)-QPointF(p2)).manhattanLength() < self.polygon_close_treshold
        
    def data_rect_for_axes(self, x_axis = xBottom, y_axis = yLeft):
        if x_axis in self.axes and y_axis in self.axes:
            x_min, x_max = self.bounds_for_axis(x_axis, try_auto_scale=False)
            y_min, y_max = self.bounds_for_axis(y_axis, try_auto_scale=False)
            if x_min and x_max and y_min and y_max:
                return QRectF(x_min, y_min, x_max-x_min, y_max-y_min)
        r = self.dataRectForAxes(x_axis, y_axis)
        for id, axis in self.axes.iteritems():
            if id not in CartesianAxes and axis.data_line:
                r |= QRectF(axis.data_line.p1(), axis.data_line.p2())
        ## We leave a 5% margin on each side so the graph doesn't look overcrowded
        ## TODO: Perhaps change this from a fixed percentage to always round to a round number
        dx = r.width()/20.0
        dy = r.height()/20.0
        r.adjust(-dx, -dy, dx, dy)
        return r
        
    def transform_for_axes(self, x_axis = xBottom, y_axis = yLeft):
        if not (x_axis, y_axis) in self._transform_cache:
            # We must flip the graph area, becase Qt coordinates start from top left, while graph coordinates start from bottom left
            a = QRectF(self.graph_area)
            t = a.top()
            a.setTop(a.bottom())
            a.setBottom(t)
            self._transform_cache[(x_axis, y_axis)] = self.transform_from_rects(self.data_rect_for_axes(x_axis, y_axis), a)
        return self._transform_cache[(x_axis, y_axis)]
        
    def transform(self, axis_id, value):
        if axis_id in XAxes:
            size = self.graph_area.width()
            margin = self.graph_area.left()
        else:
            size = self.graph_area.height()
            margin = self.graph_area.top()
        m, M = self.bounds_for_axis(axis_id)
        if m is None or M is None or M == m:
            return 0
        else:
            return margin + (value-m)/(M-m) * size
        
    def invTransform(self, axis_id, value):
        if axis_id in XAxes:
            size = self.graph_area.width()
            margin = self.graph_area.left()
        else:
            size = self.graph_area.height()
            margin = self.graph_area.top()
        m, M = self.bounds_for_axis(axis_id)
        if m is not None and M is not None:
            return m + (value-margin)/size * (M-m)
        else:
            return 0
        
    def bounds_for_axis(self, axis_id, try_auto_scale=True):
        if axis_id in self.axes:
            if self.axes[axis_id].scale:
                m, M, t = self.axes[axis_id].scale
                return m, M
            elif self.axes[axis_id].labels:
                return -0.2, len(self.axes[axis_id].labels) - 0.8
        if try_auto_scale:
            return self.boundsForAxis(axis_id)
        else:
            return None, None
            
    def enableYRaxis(self, enable=1):
        self.set_axis_enabled(yRight, enable)
        
    def enableXaxis(self, enable=1):
        self.set_axis_enabled(xBottom, enable)
        
    def set_axis_enabled(self, axis, enable):
        if axis not in self.axes:
            self.add_axis(axis)
        self.axes[axis].setVisible(enable)
        self.replot()

    @staticmethod
    def axis_coordinate(point, axis_id):
        if axis_id in XAxes:
            return point.x()
        elif axis_id in YAxes:
            return point.y()
        else:
            return None