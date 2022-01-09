from genie.core.global_const import GenieMethod

from PyQt5 import QtWidgets, QtCore


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

    def __init__(self, genie, parent=None):
        super().__init__(parent)

        # menus
        self.file = FileMenu(genie, self)
        self.inversions = InversionsMenu(genie, self)
        self.view = ViewMenu(genie, self)
        self.action = ActionMenu(genie, self)

        # add menus to main menu
        self.addAction(self.file.menuAction())
        self.addAction(self.inversions.menuAction())
        self.addAction(self.view.menuAction())
        self.addAction(self.action.menuAction())


class FileMenu(QtWidgets.QMenu):
    def __init__(self, genie, parent=None):
        super().__init__(parent)
        self.setTitle("File")

        # app actions
        self.actionNewProject = create_action(self, "New project...")
        self.actionOpenProject = create_action(self, "Open project...")
        self.actionSaveProject = create_action(self, "Save project")
        self.actionCloseProject = create_action(self, "Close project")
        self.actionImportExcel = create_action(self, "Import excel file...")
        self.actionImportFirstArrivals = create_action(self, "Import first arrivals...")
        self.actionImportPointCloud = create_action(self, "Import point cloud...")
        self.actionImportGalleryMesh = create_action(self, "Import gallery mesh...")
        self.actionImportMap = create_action(self, "Import map...")
        self.actionExit = create_action(self, "Exit", "Ctrl+Q")

        # add actions to menu
        self.addAction(self.actionNewProject)
        self.addAction(self.actionOpenProject)
        #self.addAction(self.actionSaveProject)
        self.addAction(self.actionCloseProject)
        self.addSeparator()
        self.addAction(self.actionImportExcel)
        if genie.method == GenieMethod.ST:
            self.addAction(self.actionImportFirstArrivals)
        self.addAction(self.actionImportPointCloud)
        self.addAction(self.actionImportGalleryMesh)
        self.addAction(self.actionImportMap)
        #self.addSeparator()
        #self.addAction(self.actionExit)


class ViewMenu(QtWidgets.QMenu):
    def __init__(self, genie, parent=None):
        super().__init__(parent)
        self.setTitle("View")

        # app actions
        self.actionElectrodes = create_action(self, "Electrodes")
        self.actionMeshCutTool = create_action(self, "Mesh cut tool")
        self.actionSideView = create_action(self, "Side view")
        self.actionMeasurements = create_action(self, "Measurements")

        # add actions to menu
        self.addAction(self.actionElectrodes)
        self.addAction(self.actionMeshCutTool)
        self.addAction(self.actionSideView)
        self.addAction(self.actionMeasurements)


class InversionsMenu(QtWidgets.QMenu):
    inversion_selected = QtCore.pyqtSignal(str)

    def __init__(self, genie, parent=None):
        super().__init__(parent)
        self.setTitle("Inversions")

        self.genie = genie

        # app actions
        self.actionEdit = create_action(self, "Edit...")

        # add actions to menu
        self.addAction(self.actionEdit)
        self.addSeparator()

        self._group = QtWidgets.QActionGroup(self)
        #self._group.setExclusive(True)
        self._group.triggered.connect(self._inv_selected)
        self._actions = []
        self.aboutToShow.connect(self.reload_inversions)

    def reload_inversions(self):
        for action in self._actions:
            self.removeAction(action)
            self._group.removeAction(action)
        self._actions = []

        for inversion_name in self.genie.project_cfg.inversions:
            action = QtWidgets.QAction(inversion_name, self, checkable=True)
            action.setData(inversion_name)
            action.setChecked(self.genie.project_cfg.curren_inversion_name == inversion_name)
            self.addAction(action)
            self._group.addAction(action)
            self._actions.append(action)

        for action in self._actions:
            self.addAction(action)

    def _inv_selected(self, a):
        action = self._group.checkedAction()
        inversion_name = action.data()
        self.inversion_selected.emit(inversion_name)


class ActionMenu(QtWidgets.QMenu):
    def __init__(self, genie, parent=None):
        super().__init__(parent)
        self.setTitle("Action")

        # app actions
        self.actionAnalyseMeasurement = create_action(self, "Analyse measurement...")
        self.actionFirstArrivalEditor = create_action(self, "First arrival editor...")

        # add actions to menu
        if genie.method == GenieMethod.ERT:
            self.addAction(self.actionAnalyseMeasurement)
        else:
            self.addAction(self.actionFirstArrivalEditor)
