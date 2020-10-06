from .menus.main_menu_bar import MainMenuBar
from .tab_widget import TabWidget
from genie.core.global_const import GenieMethod

from PyQt5 import QtWidgets

import os


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, genie):
        super().__init__()

        if genie.method == GenieMethod.ERT:
            self.app_name = "Genie ERT"
        elif genie.method == GenieMethod.ST:
            self.app_name = "Genie ST"
        else:
            self.app_name = ""

        self.setWindowTitle(self.app_name)

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
                self.setWindowTitle("{} - {} - {}".format(project_text, name, self.app_name))
            else:
                self.setWindowTitle("{} - {}".format(project_text, name, self.app_name))
        else:
            self.setWindowTitle(self.app_name)

    def closeEvent(self, event):
        self.tab_wiget.inv_prep._handle_save_project_action()
        super(MainWindow, self).closeEvent(event)
