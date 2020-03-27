from PyQt5 import QtWidgets
from ui.tabs.inversion_preparation import InversionPreparation
from ui.tabs.view_3d import View3D


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, main_window, parent=None):
        super(TabWidget, self).__init__(parent)
        self.addTab(InversionPreparation(main_window), "Inversion Preparation")
        self.addTab(View3D(), "Inversion 3D View")


