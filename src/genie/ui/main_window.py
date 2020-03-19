from PyQt5.QtCore import Qt
from ui.panels.scene import DiagramView
import electrode_parser
from ui.panels.electrode_views import ElectrodeGroupModel, ElectrodeGroupView
from ui.panels.measurement_view import MeasurementModel, MeasurementGroupView
from ui.panels.region_panel import RegionPanel
from ui.menus.main_menu_bar import MainMenuBar
from ui.dialogs.new_project_dialog import NewProjectDialog
from ui.dialogs.edit_inversions_dialog import EditInversionsDialog
#import ert_prepare
#from run_inv import RunInvDlg
from ui.dialogs.gen_mesh_dialog import GenerateMeshDlg

from PyQt5 import QtWidgets, QtCore

from ui.panels.measurement_view import MeasurementGroupView


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, genie):
        super().__init__()

        self.setWindowTitle("Genie")

        self.resize(1200, 800)
        central_widget = QtWidgets.QWidget(self)
        self._init_docks()

        file_name = "res/seznam souřadnic ERT bukov_finale_pb 4.xlsx"
        res = electrode_parser.parse(file_name)
        self._electrode_groups = res["electrode_groups"]
        self._measurements = res["measurements"]

        self._electrode_group_model = ElectrodeGroupModel(self._electrode_groups)

        self.el_group_view = ElectrodeGroupView(self, self._electrode_group_model)
        self.edit_electrodes.setWidget(self.el_group_view)
        self.el_group_view.setMinimumWidth(200)
        self.el_group_view.setMaximumWidth(400)

        self.diagram_view = DiagramView()
        self.setCentralWidget(self.diagram_view)

        self.region_panel = RegionPanel(self, self.diagram_view._scene)
        self.region_panel._update_region_list()
        self.region_panel_dock.setWidget(self.region_panel)

        self.region_panel.region_changed.connect(self.diagram_view._scene.region_panel_changed)
        self.diagram_view._scene.selection_changed.connect(self.region_panel.selection_changed)

        self._measurement_model = MeasurementModel(self._measurements)

        self.measurement_view = MeasurementGroupView(self, self._measurement_model)
        self.measurements_dock.setWidget(self.measurement_view)
        self.measurement_view.setMinimumWidth(200)
        self.measurement_view.setMaximumWidth(400)


        self.diagram_view.show_electrodes(self._electrode_groups)
        #self.diagram_view.show_laser("/home/radek/work/Genie/laser/BUK_20160907_JTSK_zkr_1cm.txt")
        #self.region_panel.selection_changed()

        self.diagram_view.show_map()
        self.diagram_view.fitInView(self.diagram_view._scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

        # menuBar
        self.menuBar = MainMenuBar(self)
        self.setMenuBar(self.menuBar)

        # connect actions
        self.menuBar.file.actionExit.triggered.connect(QtWidgets.QApplication.quit)
        self.menuBar.file.actionNewProject.triggered.connect(self._handle_new_project_action)
        self.menuBar.inversions.actionEdit.triggered.connect(self._handle_inversions_edit_action)

    def _init_docks(self):
        """Initializes docks"""
        self.edit_electrodes = QtWidgets.QDockWidget("Electrodes", self)
        self.edit_electrodes.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.edit_electrodes)

        self.region_panel_dock = QtWidgets.QDockWidget("Regions", self)
        self.region_panel_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.region_panel_dock)
        #self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)

        self.measurements_dock = QtWidgets.QDockWidget("Measurements", self)
        self.measurements_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.measurements_dock)

    def _handle_new_project_action(self):
        dlg = NewProjectDialog(self)
        dlg.exec()

    def _handle_inversions_edit_action(self):
        dlg = EditInversionsDialog(self)
        dlg.exec()

    # def _handle_el_groupList_item_change(self):
    #     currentItem = self.el_groupView.currentItem()
    #     if currentItem:
    #         self.show_electrodes(currentItem.text())

    # def load_electrodes(self):
    #     electrode_list = electrode_parser.parse("seznam souřadnic ERT bukov_finale_ff.xlsx")
    #     return
    #     self.electrode_dict = {e.id: e for e in electrode_list}
    #
    #     self.electrode_group_dict = {}
    #     for k, v in self.electrode_dict.items():
    #         gk = "{}, {}, {}".format(v.dilo, v.wall.name, v.height)
    #         if gk in self.electrode_group_dict:
    #             self.electrode_group_dict[gk].append(v)
    #         else:
    #             self.electrode_group_dict[gk] = [v]

    # def show_electrode_groups(self):
    #     self.el_groupView.clear()
    #     self.el_groupView.addItems(sorted(self.electrode_group_dict.keys()))

    # def show_electrodes(self, key):
    #     self.electrodeList.clear()
    #     self.electrodeList.addItems(sorted(["{}, {}, {}, {}, {}".format(e.id, e.metraz, e.x, e.y, e.z) for e in self.electrode_group_dict[key]]))

    def _handle_run_invButton(self):
        measurements = self._measurement_model.checkedMeasurements()
        if measurements:
            print(measurements)
            #data = ert_prepare.prepare(self._electrode_groups, measurements)
            #data.save("out.dat")
            from run_inv import RunInvDlg
            dlg = RunInvDlg(self._electrode_groups, measurements, self)
            dlg.exec()

    def _handle_connect_electrodesButton(self):
        sel = self.el_group_view.view.selectedIndexes()
        if sel:
            eg = self._electrode_groups[sel[0].row()]
            self.diagram_view.connect_electrodes(eg)

    def _handle_generate_meshButton(self):
        dlg = GenerateMeshDlg(self.diagram_view._scene.decomposition, self)
        dlg.exec()
