import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from genie.ui.panels.scene import DiagramView, Cursor
from genie.ui.main_window import MainWindow
from genie.core import config_file
from genie.core.config import GenieConfig

from PyQt5 import QtCore, QtGui, QtWidgets


class Genie:
    def __init__(self):
        self.cfg = GenieConfig()
        self.project_cfg = None
        self.current_inversion_cfg = None

    def load_cfg(self):
        cfg = None#config_file.get_config_file("genie", cls=GenieConfig, extension="conf")
        if cfg is None:
            self.cfg = GenieConfig()
        else:
            self.cfg = cfg

        self.cfg.current_project_dir = ""

    def save_cfg(self):
        #config_file.save_config_file("genie", self.cfg, extension="conf")
        pass


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Cursor.setup_cursors()
    genie = Genie()
    genie.load_cfg()
    mainWindow = MainWindow(genie)
    mainWindow.setGeometry(400, 200, 1200, 800)
    mainWindow.show()
    ret = app.exec()
    genie.save_cfg()
    sys.exit(ret)
