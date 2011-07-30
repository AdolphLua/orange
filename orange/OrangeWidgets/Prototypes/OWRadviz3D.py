"""
<name>RadViz 3D</name>
<icon>icons/Radviz.png</icon>
<priority>2000</priority>
"""

from OWVisWidget import *
from plot.owplot3d import *
from OWkNNOptimization import OWVizRank
from OWFreeVizOptimization import *
import OWToolbars, OWGUI, orngTest
import orngVizRank

class OWRadviz3DPlot(OWPlot3D, orngScaleLinProjData):
    def __init__(self, widget, parent=None, name='None'):
        OWPlot3D.__init__(self, parent)
        orngScaleLinProjData.__init__(self)

        self.show_value_lines = False
        self.value_line_length = 0
        self.use_different_symbols = True
        self.use_different_colors = True
        self.send_selection_on_update = False

    def set_data(self, data, subset_data=None, **args):
        orngScaleLinProjData.setData(self, data, subset_data, **args)

class OWRadviz3D(OWVisWidget):
    settingsList = ['showAllAttributes']
    jitter_size_nums = [0.0, 0.01, 0.1, 0.5, 1, 2, 3, 4, 5, 7, 10, 15, 20]

    def __init__(self, parent=None, signalManager=None):
        name = 'Radviz'
        OWVisWidget.__init__(self, parent, signalManager, 'Radviz', TRUE)

        self.inputs = [("Examples", ExampleTable, self.set_data, Default),
                       ("Example Subset", ExampleTable, self.set_subset_data),
                       ("Attribute Selection List", AttributeList, self.set_shown_attributes),
                       ("Evaluation Results", orngTest.ExperimentResults, self.set_test_results),
                       ("VizRank Learner", orange.Learner, self.set_vizrank_learner)]
        self.outputs = [("Selected Examples", ExampleTable),
                        ("Unselected Examples", ExampleTable),
                        ("Attribute Selection List", AttributeList)]

        self.showAllAttributes = 0
        self.showSelectedAttributes = 0
        self.auto_send_selection = 0

        self.plot = OWRadviz3DPlot(self, self.mainArea, name)
        self.mainArea.layout().addWidget(self.plot)

        self.vizrank = OWVizRank(self, self.signalManager, self.plot, orngVizRank.RADVIZ, name)
        self.connect(self.graphButton, SIGNAL("clicked()"), self.save_to_file)

        self.tabs = OWGUI.tabWidget(self.controlArea)
        self.general_tab = OWGUI.createTabPage(self.tabs, 'Main')
        self.settings_tab = OWGUI.createTabPage(self.tabs, 'Settings', canScroll=1)

        self.createShowHiddenLists(self.general_tab, callback=self.update_plot_and_anchors)

        self.optimization_buttons = OWGUI.widgetBox(self.general_tab, "Optimization Dialogs", orientation="horizontal")
        self.vizrank_button = OWGUI.button(self.optimization_buttons, self, "VizRank", callback=self.vizrank.reshow,
            tooltip="Opens VizRank dialog, where you can search for interesting projections with different subsets of attributes.",
            debuggingEnabled=0)

        self.wd_child_dialogs = [self.vizrank]

        self.free_viz_dlg = FreeVizOptimization(self, self.signalManager, self.plot, name)
        self.wd_child_dialogs.append(self.free_viz_dlg)
        self.free_viz_dlg_button = OWGUI.button(self.optimization_buttons,
            self, 'FreeViz', callback=self.free_viz_dlg.reshow,
            tooltip="Opens FreeViz dialog, where the position of attribute anchors is optimized so that class separation is improved",
            debuggingEnabled=0)
        self.zoom_select_toolbar = OWToolbars.ZoomSelectToolbar(self, self.general_tab, self.plot, self.auto_send_selection)
        self.plot.auto_send_selection_callback = self.selection_changed
        self.connect(self.zoom_select_toolbar.buttonSendSelections, SIGNAL("clicked()"), self.send_selections)

        self.extra_top_box = OWGUI.widgetBox(self.settings_tab, orientation="vertical")
        self.extra_top_box.hide()

        #self.plot.gui.point_properties_box(self.SettingsTab)

        box = OWGUI.widgetBox(self.settings_tab, "Jittering Options")
        OWGUI.comboBoxWithCaption(box, self, "plot.jitter_size", 'Jittering size (% of range):',
            callback=self.reset_plot_data, items=self.jitter_size_nums, sendSelectedValue=1, valueType=float)
        OWGUI.checkBox(box, self, 'plot.jitter_continuous',
            'Jitter continuous attributes',
            callback=self.reset_plot_data,
            tooltip="Does jittering apply also on continuous attributes?")

        box = OWGUI.widgetBox(self.settings_tab, "Scaling Options")
        OWGUI.qwtHSlider(box, self, "plot.scale_factor",
            label='Inflate points by: ',
            minValue=1.0, maxValue= 10.0, step=0.1,
            callback=self.update_plot,
            tooltip="If points lie too much together you can expand their position to improve perception",
            maxWidth=90)

        box = OWGUI.widgetBox(self.settings_tab, "General Graph Settings")
        #self.graph.gui.show_legend_check_box(box)
        bbox = OWGUI.widgetBox(box, orientation="horizontal")
        OWGUI.checkBox(bbox, self, 'plot.show_value_lines', 'Show value lines  ', callback=self.update_plot)
        OWGUI.qwtHSlider(bbox, self, 'plot.value_line_length', minValue=1, maxValue=10, step=1, callback=self.update_plot, showValueLabel=0)
        OWGUI.checkBox(box, self, 'plot.use_different_symbols', 'Use different symbols', callback=self.update_plot,
            tooltip="Show different class values using different symbols")
        OWGUI.checkBox(box, self, 'plot.use_different_colors', 'Use different colors',
            callback=self.update_plot, tooltip="Show different class values using different colors")

        box = OWGUI.widgetBox(self.settings_tab, "Colors", orientation="horizontal")
        OWGUI.button(box, self, "Colors", self.set_colors,
            tooltip="Set the canvas background color and color palette for coloring variables",
            debuggingEnabled=0)

        self.tooltip_kind = 0
        self.tooltip_value = 0
        box = OWGUI.widgetBox(self.settings_tab, "Tooltips Settings")
        OWGUI.comboBox(box, self, "tooltip_kind",
            items=["Show line tooltips", "Show visible attributes", "Show all attributes"],
            callback=self.update_plot)
        OWGUI.comboBox(box, self, "tooltip_value",
            items=["Tooltips show data values", "Tooltips show spring values"],
            callback=self.update_plot,
            tooltip="Do you wish that tooltips would show you original values of visualized"+\
                    "attributes or the 'spring' values (values between 0 and 1). \nSpring values "+\
                    "are scaled values that are used for determining the position of shown points."+\
                    "Observing these values will therefore enable you to \nunderstand why the points are placed where they are.")

        self.auto_send_selection = 0
        self.add_projected_positions = 0
        box = OWGUI.widgetBox(self.settings_tab, "Auto Send Selected Data When...")
        OWGUI.checkBox(box, self, 'auto_send_selection', 'Adding/Removing selection areas',
            callback=self.selection_changed, tooltip="Send selected data whenever a selection area is added or removed")
        OWGUI.checkBox(box, self, 'plot.send_selection_on_update', 'Moving/Resizing selection areas',
            tooltip="Send selected data when a user moves or resizes an existing selection area")
        OWGUI.comboBox(box, self, "add_projected_positions",
            items=["Do not modify the domain", "Append projection as attributes", "Append projection as meta attributes"],
            callback=self.send_selections)
        self.selection_changed()

        self.settings_tab.layout().addStretch(100)
        self.resize(900, 700)

    def selection_changed(self):
        pass

    def update_plot_and_anchors(self):
        pass

    def send_selections(self):
        pass

    def reset_plot_data(self):
        pass

    def update_plot(self):
        pass

    updateGraph = update_plot

    def set_colors(self):
        pass

    def set_data(self, data):
        self.data = data

    def set_subset_data(self, subset_data):
        self.subset_data = subset_data

    def set_shown_attributes(self, attrs):
        pass

    def set_test_results(self, results):
        pass

    def set_vizrank_learner(self, leaner):
        pass

    def save_to_file(self, file):
        pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    radviz = OWRadviz3D()
    radviz.show()
    data = orange.ExampleTable('../../doc/datasets/iris')
    radviz.set_data(data)
    radviz.handleNewSignals()
    app.exec_()
