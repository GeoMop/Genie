from scene import DiagramView, Cursor
from main_window import MainWindow

from PyQt5 import QtCore, QtGui, QtWidgets

import sys


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Cursor.setup_cursors()
    mainWindow = MainWindow()
    #mainWindow.setGeometry(400, 200, 1200, 800)
    mainWindow.show()
    sys.exit(app.exec())
