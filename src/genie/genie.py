from scene import DiagramView, Cursor
from main_window import MainWindow
import config_file
from config import GenieConfig

from PyQt5 import QtCore, QtGui, QtWidgets

import sys


class Genie:
    def __init__(self):
        self.cfg = GenieConfig()

    def load_cfg(self):
        cfg = config_file.get_config_file("genie", cls=GenieConfig, extension="conf")
        if cfg is None:
            self.cfg = GenieConfig()
        else:
            self.cfg = cfg

    def save_cfg(self):
        config_file.save_config_file("genie", self.cfg, extension="conf")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Cursor.setup_cursors()
    genie = Genie()
    genie.load_cfg()
    mainWindow = MainWindow(genie)
    #mainWindow.setGeometry(400, 200, 1200, 800)
    mainWindow.show()
    ret = app.exec()
    genie.save_cfg()
    sys.exit(ret)
