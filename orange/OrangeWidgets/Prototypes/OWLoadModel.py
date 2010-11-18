"""<name>Load Model</name>
"""

from OWWidget import *
import OWGUI
import orange


class OWLoadModel(OWWidget):
    settingsList = ["filenameHistory", "selectedFileIndex", "lastFile"]
    
    def __init__(self, parent=None, signalManager=None, name="Load Model"):
        OWWidget.__init__(self, parent, signalManager, name, wantMainArea=False)
        
        self.outputs = [("Classifier", orange.Classifier)]
        
        self.filenameHistory = []
        self.selectedFileIndex = 0
        self.lastFile = os.path.expanduser("~/orange_model.pck")
        
        self.loadSettings()
        
        #####
        # GUI
        #####
        
        box = OWGUI.widgetBox(self.controlArea, "File", orientation="horizontal", addSpace=True)
        self.filesCombo = OWGUI.comboBox(box, self, "selectedFileIndex", 
                                         items = [os.path.basename(p) for p in self.filenameHistory],
                                         tooltip="Select a recent file", 
                                         callback=self.onRecentSelection)
        
        self.browseButton = OWGUI.button(box, self, "...", callback=self.browse,
                                         tooltip = "Browse file system")

        self.browseButton.setIcon(self.style().standardIcon(QStyle.SP_DirOpenIcon))
        self.browseButton.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        
        OWGUI.rubber(self.controlArea)
        
        self.resize(200, 50)
        
        
    def onRecentSelection(self):
        filename = self.filenameHistory[self.selectedFileIndex]
        self.filenameHistory.pop(self.selectedFileIndex)
        self.filenameHistory.insert(0, filename)
        self.filesCombo.removeItem(self.selectedFileIndex)
        self.filesCombo.insertItem(0, os.path.basename(filename))
        self.selectedFileIndex = 0
        
        self.loadAndSend()
        
    def browse(self):
        filename = QFileDialog.getOpenFileName(self, "Load Model From File",
                        self.lastFile, "Pickle files (*.pickle *.pck)\nAll files (*.*)")
        filename = str(filename)
        if filename:
            if filename in self.filenameHistory:
                self.selectedFileIndex = self.filenameHistory.index(filename)
                self.onRecentSelection()
                return
            self.lastFile = filename
            self.filenameHistory.insert(0, filename)
            self.filesCombo.insertItem(0, os.path.basename(filename))
            self.filesCombo.setCurrentIndex(0)
            self.loadAndSend()
            
    def loadAndSend(self):
        filename = self.filenameHistory[self.selectedFileIndex]
        import cPickle
        self.error([0, 1])
        try:
            model = cPickle.load(open(filename, "rb"))
        except Exception, ex:
            self.error(0, "Could not load model! %s" % str(ex))
            return
        
        if not isinstance(model, orange.Classifier):
            self.error(1, "'%s' is not an orange classifier" % os.path.basename(filename))
            return 
        
        self.send("Classifier", model)
        
if __name__ == "__main__":
    app = QApplication([])
    w = OWLoadModel()
    w.show()
    app.exec_()
    w.saveSettings() 