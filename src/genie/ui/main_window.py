from .menus.main_menu_bar import MainMenuBar
from .tab_widget import TabWidget

from PyQt5 import QtWidgets, QtCore

import os


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, genie):
        super().__init__()

        self.setWindowTitle("Genie")

        self.resize(1200, 800)

        # menuBar
        self.menuBar = MainMenuBar(genie, self)
        self.setMenuBar(self.menuBar)

        self.tab_wiget = TabWidget(self, genie)
        self.setCentralWidget(self.tab_wiget)

        # status bar
        self._inversion_label = QtWidgets.QLabel(self)
        self._status = self.statusBar()
        self._status.addPermanentWidget(self._inversion_label)
        self.set_current_inversion("")

    def set_current_inversion(self, name, project_path=""):
        if project_path:
            project_text = "{} - [{}]".format(os.path.basename(project_path), project_path)
            project_text_status = "{} [{}]".format(os.path.basename(project_path), project_path)
        else:
            project_text = ""
            project_text_status = ""

        self._inversion_label.setText("Project: {}, Inversion: {}".format(project_text_status, name))

        if project_path:
            if name:
                self.setWindowTitle("{} - {} - Genie".format(project_text, name))
            else:
                self.setWindowTitle("{} - Genie".format(project_text, name))
        else:
            self.setWindowTitle("Genie")

    def closeEvent(self, event):
        self.tab_wiget.inv_prep._handle_save_project_action()
        super(MainWindow, self).closeEvent(event)
