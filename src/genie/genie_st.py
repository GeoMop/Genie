import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from genie.ui.panels.scene import Cursor
from genie.ui.main_window import MainWindow
from genie.core import config_file
from genie.core.config import GenieConfig
from genie.core.global_const import GenieMethod

from PyQt5 import QtWidgets, QtCore


class Genie:
    def __init__(self):
        self.cfg = GenieConfig()
        self.project_cfg = None
        self.current_inversion_cfg = None
        self.method = GenieMethod.ST

    def load_cfg(self):
        try:
            cfg = config_file.get_config_file("genie_st", cls=GenieConfig, extension="conf")
        except Exception:
            cfg = None

        if cfg is None:
            self.cfg = GenieConfig()
        else:
            self.cfg = cfg

        self.cfg.current_project_dir = ""

    def save_cfg(self):
        config_file.save_config_file("genie_st", self.cfg, extension="conf")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    locale = QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates)
    locale.setNumberOptions(QtCore.QLocale.RejectGroupSeparator)
    QtCore.QLocale.setDefault(locale)

    Cursor.setup_cursors()
    genie = Genie()
    genie.load_cfg()
    mainWindow = MainWindow(genie)
    mainWindow.setGeometry(400, 200, 1200, 800)
    mainWindow.show()
    ret = app.exec()
    genie.save_cfg()
    sys.exit(ret)
