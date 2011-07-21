"""<name> 3D Scatterplot</name>
"""

from OWWidget import *
from owplot3d import *

import OWGUI
import OWToolbars
import OWColorPalette

import numpy

TooltipKind = enum('NONE', 'VISIBLE', 'ALL') # Which attributes should be displayed in tooltips?

class OWScatterPlot3D(OWWidget):
    settingsList = ['plot.show_legend', 'plot.symbol_size', 'plot.show_x_axis_title', 'plot.show_y_axis_title',
                    'plot.show_z_axis_title', 'plot.show_legend', 'plot.face_symbols', 'plot.filled_symbols',
                    'plot.transparency', 'plot.show_grid', 'plot.pitch', 'plot.yaw', 'plot.use_ortho',
                    'auto_send_selection', 'auto_send_selection_update']
    contextHandlers = {"": DomainContextHandler("", ["xAttr", "yAttr", "zAttr"])}
    jitter_sizes = [0.0, 0.1, 0.5, 1, 2, 3, 4, 5, 7, 10, 15, 20, 30, 40, 50]

    def __init__(self, parent=None, signalManager=None, name="Scatter Plot 3D"):
        OWWidget.__init__(self, parent, signalManager, name, True)

        self.inputs = [("Examples", ExampleTable, self.set_data, Default), ("Subset Examples", ExampleTable, self.set_subset_data)]
        self.outputs = [("Selected Examples", ExampleTable), ("Unselected Examples", ExampleTable)]

        self.x_attr = 0
        self.y_attr = 0
        self.z_attr = 0

        self.color_attr = None
        self.size_attr = None
        self.shape_attr = None
        self.label_attr = None

        self.symbol_scale = 5
        self.alpha_value = 255

        self.loadSettings()

        self.tabs = OWGUI.tabWidget(self.controlArea)
        self.main_tab = OWGUI.createTabPage(self.tabs, 'Main')
        self.settings_tab = OWGUI.createTabPage(self.tabs, 'Settings', canScroll=True)

        self.x_attr_cb = OWGUI.comboBox(self.main_tab, self, "x_attr", box="X-axis attribute",
            tooltip="Attribute to plot on X axis.",
            callback=self.on_axis_change
            )

        self.y_attr_cb = OWGUI.comboBox(self.main_tab, self, "y_attr", box="Y-axis attribute",
            tooltip="Attribute to plot on Y axis.",
            callback=self.on_axis_change
            )

        self.z_attr_cb = OWGUI.comboBox(self.main_tab, self, "z_attr", box="Z-axis attribute",
            tooltip="Attribute to plot on Z axis.",
            callback=self.on_axis_change
            )

        self.color_attr_cb = OWGUI.comboBox(self.main_tab, self, "color_attr", box="Point color",
            tooltip="Attribute to use for point color",
            callback=self.on_axis_change)

        # Additional point properties (labels, size, shape).
        additional_box = OWGUI.widgetBox(self.main_tab, 'Additional Point Properties')
        self.size_attr_cb = OWGUI.comboBox(additional_box, self, "size_attr", label="Point size:",
            tooltip="Attribute to use for pointSize",
            callback=self.on_axis_change,
            indent = 10,
            emptyString = '(Same size)',
            )

        self.shape_attr_cb = OWGUI.comboBox(additional_box, self, "shape_attr", label="Point shape:",
            tooltip="Attribute to use for pointShape",
            callback=self.on_axis_change,
            indent = 10,
            emptyString = '(Same shape)',
            )

        self.label_attr_cb = OWGUI.comboBox(additional_box, self, "label_attr", label="Point label:",
            tooltip="Attribute to use for pointLabel",
            callback=self.on_axis_change,
            indent = 10,
            emptyString = '(No labels)'
            )

        self.plot = OWPlot3D(self)

        box = OWGUI.widgetBox(self.settings_tab, 'Point properties')
        OWGUI.hSlider(box, self, "plot.symbol_scale", label="Symbol scale",
            minValue=1, maxValue=5,
            tooltip="Scale symbol size",
            callback=self.on_checkbox_update,
            )

        OWGUI.hSlider(box, self, "plot.transparency", label="Transparency",
            minValue=10, maxValue=255,
            tooltip="Point transparency value",
            callback=self.on_checkbox_update)
        OWGUI.rubber(box)

        self.jitter_size = 0
        self.jitter_continuous = False
        box = OWGUI.widgetBox(self.settings_tab, "Jittering Options")
        self.jitter_size_combo = OWGUI.comboBox(box, self, 'jitter_size', label='Jittering size (% of size)'+'  ',
            orientation='horizontal',
            callback=self.on_checkbox_update,
            items=self.jitter_sizes,
            sendSelectedValue=1,
            valueType=float)
        OWGUI.checkBox(box, self, 'jitter_continuous', 'Jitter continuous attributes',
            callback=self.on_checkbox_update,
            tooltip='Does jittering apply also on continuous attributes?')

        box = OWGUI.widgetBox(self.settings_tab, 'General settings')
        OWGUI.checkBox(box, self, 'plot.show_x_axis_title',   'X axis title',   callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.show_y_axis_title',   'Y axis title',   callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.show_z_axis_title',   'Z axis title',   callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.show_legend',         'Show legend',    callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.use_ortho',           'Use ortho',      callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.filled_symbols',      'Filled symbols', callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.face_symbols',        'Face symbols',   callback=self.on_checkbox_update)
        OWGUI.checkBox(box, self, 'plot.show_grid',           'Show grid',      callback=self.on_checkbox_update)
        OWGUI.rubber(box)

        self.auto_send_selection = True
        self.auto_send_selection_update = False
        self.plot.selection_change_callback = self.send_selections
        box = OWGUI.widgetBox(self.settings_tab, 'Auto Send Selected Data When...')
        OWGUI.checkBox(box, self, 'auto_send_selection', 'Adding/Removing selection areas',
            callback = self.on_checkbox_update, tooltip = 'Send selected data whenever a selection area is added or removed')
        OWGUI.checkBox(box, self, 'auto_send_selection_update', 'Moving/Resizing selection areas',
            callback = self.on_checkbox_update, tooltip = 'Send selected data when a user moves or resizes an existing selection area')

        self.zoom_select_toolbar = OWToolbars.ZoomSelectToolbar(self, self.main_tab, self.plot, self.auto_send_selection)
        self.connect(self.zoom_select_toolbar.buttonSendSelections, SIGNAL('clicked()'), self.send_selections)
        self.connect(self.zoom_select_toolbar.buttonSelectRect, SIGNAL('clicked()'), self.change_selection_type)
        self.connect(self.zoom_select_toolbar.buttonSelectPoly, SIGNAL('clicked()'), self.change_selection_type)
        self.connect(self.zoom_select_toolbar.buttonZoom, SIGNAL('clicked()'), self.change_selection_type)
        self.connect(self.zoom_select_toolbar.buttonRemoveLastSelection, SIGNAL('clicked()'), self.plot.remove_last_selection)
        self.connect(self.zoom_select_toolbar.buttonRemoveAllSelections, SIGNAL('clicked()'), self.plot.remove_all_selections)
        self.toolbarSelection = None

        self.tooltip_kind = TooltipKind.NONE
        box = OWGUI.widgetBox(self.settings_tab, "Tooltips Settings")
        OWGUI.comboBox(box, self, 'tooltip_kind', items = [
            'Don\'t Show Tooltips', 'Show Visible Attributes', 'Show All Attributes'], callback = self.on_axis_change)

        self.plot.mouseover_callback = self.mouseover_callback
        self.shown_attr_indices = []

        self.main_tab.layout().addStretch(100)
        self.settings_tab.layout().addStretch(100)

        self.mainArea.layout().addWidget(self.plot)
        self.connect(self.graphButton, SIGNAL("clicked()"), self.plot.save_to_file)

        self.data = None
        self.subsetData = None
        self.resize(1000, 600)

    def mouseover_callback(self, index):
        if self.tooltip_kind == TooltipKind.VISIBLE:
            self.plot.show_tooltip(self.get_example_tooltip(self.data[index], self.shown_attr_indices))
        elif self.tooltip_kind == TooltipKind.ALL:
            self.plot.show_tooltip(self.get_example_tooltip(self.data[index]))

    def get_example_tooltip(self, example, indices=None, max_indices=20):
        if indices and type(indices[0]) == str:
            indices = [self.attr_name_index[i] for i in indices]
        if not indices:
            indices = range(len(self.data.domain.attributes))

        if example.domain.classVar:
            classIndex = self.attr_name_index[example.domain.classVar.name]
            while classIndex in indices:
                indices.remove(classIndex)

        text = '<b>Attributes:</b><br>'
        for index in indices[:max_indices]:
            attr = self.attr_name[index]
            if attr not in example.domain:  text += '&nbsp;'*4 + '%s = ?<br>' % (attr)
            elif example[attr].isSpecial(): text += '&nbsp;'*4 + '%s = ?<br>' % (attr)
            else:                           text += '&nbsp;'*4 + '%s = %s<br>' % (attr, str(example[attr]))

        if len(indices) > max_indices:
            text += '&nbsp;'*4 + ' ... <br>'

        if example.domain.classVar:
            text = text[:-4]
            text += '<hr><b>Class:</b><br>'
            if example.getclass().isSpecial(): text += '&nbsp;'*4 + '%s = ?<br>' % (example.domain.classVar.name)
            else:                              text += '&nbsp;'*4 + '%s = %s<br>' % (example.domain.classVar.name, str(example.getclass()))

        if len(example.domain.getmetas()) != 0:
            text = text[:-4]
            text += '<hr><b>Meta attributes:</b><br>'
            for key in example.domain.getmetas():
                try: text += '&nbsp;'*4 + '%s = %s<br>' % (example.domain[key].name, str(example[key]))
                except: pass
        return text[:-4]

    def change_selection_type(self):
        if self.toolbarSelection < 3:
            selection_type = [SelectionType.ZOOM, SelectionType.RECTANGLE, SelectionType.POLYGON][self.toolbarSelection]
            self.plot.set_selection_type(selection_type)

    def set_data(self, data=None):
        self.closeContext("")
        self.data = data
        self.x_attr_cb.clear()
        self.y_attr_cb.clear()
        self.z_attr_cb.clear()
        self.color_attr_cb.clear()
        self.size_attr_cb.clear()
        self.shape_attr_cb.clear()
        self.label_attr_cb.clear()

        self.discrete_attrs = {}

        if self.data is not None:
            self.all_attrs = data.domain.variables + data.domain.getmetas().values()
            self.axis_candidate_attrs = [attr for attr in self.all_attrs
                if attr.varType in [orange.VarTypes.Continuous, orange.VarTypes.Discrete]]

            self.attr_name_index = {}
            for i, attr in enumerate(self.all_attrs):
                self.attr_name_index[attr.name] = i

            self.attr_name = {}
            for i, attr in enumerate(self.all_attrs):
                self.attr_name[i] = attr.name

            self.color_attr_cb.addItem('(Same color)')
            self.size_attr_cb.addItem('(Same size)')
            self.shape_attr_cb.addItem('(Same shape)')
            self.label_attr_cb.addItem('(No labels)')
            icons = OWGUI.getAttributeIcons() 
            for (i, attr) in enumerate(self.axis_candidate_attrs):
                self.x_attr_cb.addItem(icons[attr.varType], attr.name)
                self.y_attr_cb.addItem(icons[attr.varType], attr.name)
                self.z_attr_cb.addItem(icons[attr.varType], attr.name)
                self.color_attr_cb.addItem(icons[attr.varType], attr.name)
                self.size_attr_cb.addItem(icons[attr.varType], attr.name)
                self.label_attr_cb.addItem(icons[attr.varType], attr.name)
                if attr.varType == orange.VarTypes.Discrete:
                    self.discrete_attrs[len(self.discrete_attrs)+1] = (i, attr)
                    self.shape_attr_cb.addItem(icons[orange.VarTypes.Discrete], attr.name)

            array, c, w = self.data.toNumpyMA()
            if len(c):
                array = numpy.hstack((array, c.reshape(-1,1)))
            self.data_array = array

            self.x_attr, self.y_attr, self.z_attr = numpy.min([[0, 1, 2],
                                                               [len(self.axis_candidate_attrs) - 1]*3
                                                              ], axis=0)
            self.color_attr = max(len(self.axis_candidate_attrs) - 1, 0)
            self.shown_attr_indices = [self.x_attr, self.y_attr, self.z_attr, self.color_attr]
            self.openContext('', data)

    def set_subset_data(self, data=None):
        self.subsetData = data # TODO: what should scatterplot do with this?

    def handleNewSignals(self):
        self.update_plot()
        self.send_selections()

    def saveSettings(self):
        OWWidget.saveSettings(self)

    def sendReport(self):
        self.startReport('%s [%s - %s - %s]' % (self.windowTitle(), self.attr_name[self.x_attr],
                                                self.attr_name[self.y_attr], self.attr_name[self.z_attr]))
        self.reportSettings('Visualized attributes',
                            [('X', self.attr_name[self.x_attr]),
                             ('Y', self.attr_name[self.y_attr]),
                             ('Z', self.attr_name[self.z_attr]),
                             self.color_attr and ('Color', self.attr_name[self.color_attr]),
                             self.label_attr and ('Label', self.attr_name[self.label_attr]),
                             self.shape_attr and ('Shape', self.attr_name[self.shape_attr]),
                             self.size_attr  and ('Size', self.attr_name[self.size_attr])])
        self.reportSettings('Settings',
                            [('Symbol size', self.plot.symbol_scale),
                             ('Transparency', self.plot.transparency),
                             #("Jittering", self.graph.jitterSize),
                             #("Jitter continuous attributes", OWGUI.YesNo[self.graph.jitterContinuous])])
                             ])
        self.reportSection('Plot')
        self.reportImage(self.plot.save_to_file_direct, QSize(400, 400))

    def send_selections(self):
        if self.data == None:
            return
        indices = self.plot.get_selection_indices()
        selected = [1 if i in indices else 0 for i in range(len(self.data))]
        unselected = map(lambda n: 1-n, selected)
        selected = self.data.selectref(selected)
        unselected = self.data.selectref(unselected)
        self.send('Selected Examples', selected)
        self.send('Unselected Examples', unselected)

    def on_axis_change(self):
        if self.data is not None:
            self.update_plot()

    def on_checkbox_update(self):
        self.plot.updateGL()

    def update_plot(self):
        if self.data is None:
            return

        x_ind, y_ind, z_ind = self.get_axes_indices()
        X, Y, Z, mask = self.get_axis_data(x_ind, y_ind, z_ind)

        color_legend_items = []
        if self.color_attr > 0:
            color_attr = self.axis_candidate_attrs[self.color_attr - 1]
            C = self.data_array[:, self.color_attr - 1]
            if color_attr.varType == orange.VarTypes.Discrete:
                palette = OWColorPalette.ColorPaletteHSV(len(color_attr.values))
                colors = [palette[int(value)] for value in C.ravel()]
                colors = [[c.red()/255., c.green()/255., c.blue()/255., self.alpha_value/255.] for c in colors]
                palette_colors = [palette[i] for i in range(len(color_attr.values))]
                color_legend_items = [[Symbol.TRIANGLE, [c.red()/255., c.green()/255., c.blue()/255., 1], 1, title]
                    for c, title in zip(palette_colors, color_attr.values)]
            else:
                palette = OWColorPalette.ColorPaletteBW()
                maxC, minC = numpy.max(C), numpy.min(C)
                C = (C - minC) / (maxC - minC)
                colors = [palette[value] for value in C.ravel()]
                colors = [[c.red()/255., c.green()/255., c.blue()/255., self.alpha_value/255.] for c in colors]
        else:
            colors = 'b'

        if self.size_attr > 0:
            size_attr = self.axis_candidate_attrs[self.size_attr - 1]
            S = self.data_array[:, self.size_attr - 1]
            if size_attr.varType == orange.VarTypes.Discrete:
                sizes = [(v + 1) * len(size_attr.values) / (11 - self.symbol_scale) for v in S]
            else:
                min, max = numpy.min(S), numpy.max(S)
                sizes = [(v - min) * self.symbol_scale / (max-min) for v in S]
        else:
            sizes = 1

        shapes = None
        if self.shape_attr > 0:
            i, shape_attr = self.discrete_attrs[self.shape_attr]
            if shape_attr.varType == orange.VarTypes.Discrete:
                # Map discrete attribute to [0...num shapes-1]
                shapes = self.data_array[:, i]
                num_shapes = 0
                unique_shapes = {}
                for shape in shapes:
                    if shape not in unique_shapes:
                        unique_shapes[shape] = num_shapes
                        num_shapes += 1
                shapes = [unique_shapes[value] for value in shapes]

        labels = None
        if self.label_attr > 0:
            label_attr = self.axis_candidate_attrs[self.label_attr - 1]
            labels = self.data_array[:, self.label_attr - 1]

        self.plot.clear()

        num_symbols = len(Symbol)
        if self.shape_attr > 0:
            _, shape_attr = self.discrete_attrs[self.shape_attr]
            titles = list(shape_attr.values)
            for i, title in enumerate(titles):
                if i == num_symbols-1:
                    title = ', '.join(titles[i:])
                self.plot.legend.add_item(i, (0,0,0,1), 1, '{0}={1}'.format(shape_attr.name, title))
                if i == num_symbols-1:
                    break

        if color_legend_items:
            for item in color_legend_items:
                self.plot.legend.add_item(*item)

        self.plot.scatter(X, Y, Z, colors, sizes, shapes, labels)
        self.plot.set_x_axis_title(self.axis_candidate_attrs[self.x_attr].name)
        self.plot.set_y_axis_title(self.axis_candidate_attrs[self.y_attr].name)
        self.plot.set_z_axis_title(self.axis_candidate_attrs[self.z_attr].name)

        def create_discrete_map(attr_index):
            keys = range(len(self.axis_candidate_attrs[attr_index].values))
            values = self.axis_candidate_attrs[attr_index].values
            map = {}
            for key, value in zip(keys, values):
                map[key] = value
            return map

        if self.axis_candidate_attrs[self.x_attr].varType == orange.VarTypes.Discrete:
            self.plot.set_x_axis_map(create_discrete_map(self.x_attr))
        if self.axis_candidate_attrs[self.y_attr].varType == orange.VarTypes.Discrete:
            self.plot.set_y_axis_map(create_discrete_map(self.y_attr))
        if self.axis_candidate_attrs[self.z_attr].varType == orange.VarTypes.Discrete:
            self.plot.set_z_axis_map(create_discrete_map(self.z_attr))

    def get_axis_data(self, x_ind, y_ind, z_ind):
        array = self.data_array
        X, Y, Z = array[:, x_ind], array[:, y_ind], array[:, z_ind]
        return X, Y, Z, None

    def get_axes_indices(self):
        return self.x_attr, self.y_attr, self.z_attr

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = OWScatterPlot3D()
    data = orange.ExampleTable("../../doc/datasets/iris")
    w.set_data(data)
    w.handleNewSignals()
    w.show()
    app.exec_()
