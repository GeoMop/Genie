from ui.menus.main_menu_bar import MainMenuBar

from ui.tab_widget import TabWidget

from PyQt5 import QtWidgets, QtCore



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, genie):
        super().__init__()

        self.setWindowTitle("Genie")

        self.resize(1200, 800)

        # menuBar
        self.menuBar = MainMenuBar(self)
        self.setMenuBar(self.menuBar)

        self.setCentralWidget(TabWidget(self))