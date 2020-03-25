from PyQt5 import QtWidgets
from ui.tabs.inversion_preparation import InversionPreparation


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, main_window, parent=None):
        super(TabWidget, self).__init__(parent)
        self.addTab(InversionPreparation(main_window), "Inversion Preparation")


