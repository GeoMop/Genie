import PyQt5.QtWidgets as QtWidgets


def create_action(parent, text, shortcut="", object_name=""):
    action = QtWidgets.QAction(parent)
    action.setText(text)
    action.setShortcut(shortcut)
    action.setObjectName(object_name)
    return action


class MainMenuBar(QtWidgets.QMenuBar):
    """
    Main windows menu bar.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # menus
        self.file = FileMenu(self)
        self.inversions = InversionsMenu(self)
        #self.actionAnalyses = create_action(self, "Analyses")

        # add menus to main menu
        self.addAction(self.file.menuAction())
        self.addAction(self.inversions.menuAction())
        #self.addAction(self.actionAnalyses)


class FileMenu(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("File")

        # app actions
        self.actionNewProject = create_action(self, "New project...")
        self.actionOpenProject = create_action(self, "Open project...")
        self.actionCloseProject = create_action(self, "Close project")
        self.actionExit = create_action(self, "Exit", "Ctrl+Q")

        # add actions to menu
        self.addAction(self.actionNewProject)
        self.addAction(self.actionOpenProject)
        self.addAction(self.actionCloseProject)
        self.addAction(self.actionExit)


class InversionsMenu(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Inversions")

        # app actions
        self.actionEdit = create_action(self, "Edit...")
        self.inv1 = create_action(self, "inv1")

        # add actions to menu
        self.addAction(self.actionEdit)
        self.addSeparator()
        self.addAction(self.inv1)
