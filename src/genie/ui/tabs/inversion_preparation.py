from PyQt5.QtCore import Qt
from ui.panels.scene import DiagramView
import core.electrode_parser
from core.data_types import ElectrodeGroup, Electrode, Measurement
from ui.panels.electrode_views import ElectrodeGroupModel, ElectrodeGroupView
from ui.panels.measurement_view import MeasurementModel, MeasurementGroupView
from ui.panels.region_panel import RegionPanel
from ui.panels.mesh_cut_tool_panel import MeshCutToolPanel
from ui.menus.main_menu_bar import MainMenuBar
from ui.dialogs.new_project_dialog import NewProjectDialog
from xlsreader.xls_reader import XlsReaderDialog
from ui.dialogs.point_cloud_reader import PointCloudReaderDialog
from ui.dialogs.edit_inversions_dialog import EditInversionsDialog
#import ert_prepare
#from run_inv import RunInvDlg
from ui.dialogs.gen_mesh_dialog import GenerateMeshDlg
from core.global_const import GENIE_PROJECT_FILE_NAME
from core.config import ProjectConfig, InversionConfig

from PyQt5 import QtWidgets, QtCore

from ui.panels.measurement_view import MeasurementGroupView

import os
import json
import shutil


class InversionPreparation(QtWidgets.QMainWindow):
    def __init__(self, main_window, genie, tab_wiget):
        super().__init__()
        self.main_window = main_window
        self.genie = genie
        self.tab_wiget = tab_wiget
        self._init_docks()
        #self.setStyleSheet("QMainWindow {background: 'lightgray';}");

        self._electrode_groups = []
        self._measurements = []

        self._electrode_group_model = ElectrodeGroupModel(self._electrode_groups)

        self.el_group_view = ElectrodeGroupView(self, self._electrode_group_model)
        self.edit_electrodes.setWidget(self.el_group_view)
        self.el_group_view.setMinimumWidth(200)
        self.el_group_view.setMaximumWidth(400)

        self.diagram_view = DiagramView()
        self.setCentralWidget(self.diagram_view)

        # self.region_panel = RegionPanel(self, self.diagram_view._scene)
        # self.region_panel._update_region_list()
        # self.region_panel_dock.setWidget(self.region_panel)
        #
        # self.region_panel.region_changed.connect(self.diagram_view._scene.region_panel_changed)
        # self.diagram_view._scene.selection_changed.connect(self.region_panel.selection_changed)

        self.mesh_cut_tool_panel = MeshCutToolPanel(self, self.diagram_view._scene)
        self.mesh_cut_tool_panel.scene_cut_changed()
        self.mesh_cut_tool_panel_dock.setWidget(self.mesh_cut_tool_panel)

        self.diagram_view._scene.mesh_cut_tool_changed.connect(self.mesh_cut_tool_panel.scene_cut_changed)
        #self.diagram_view._scene.mesh_cut_tool_changed.connect(self._scene_cut_changed)

        self._measurement_model = MeasurementModel(self._measurements)

        self.measurement_view = MeasurementGroupView(self, self._measurement_model)
        self.measurements_dock.setWidget(self.measurement_view)
        self.measurement_view.setMinimumWidth(200)
        self.measurement_view.setMaximumWidth(400)

        self.diagram_view.show_electrodes(self._electrode_groups)
        #self.diagram_view.show_laser2("/home/radek/work/Genie/laser/BUK_20160907_JTSK_zkr_1cm.txt")
        #self.diagram_view.show_laser_mesh("/home/radek/work/Genie/laser/mesh.msh")
        # self.region_panel.selection_changed()

        self.diagram_view.show_map()
        self.diagram_view.fitInView(self.diagram_view._scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

        # connect actions
        self.main_window.menuBar.file.actionExit.triggered.connect(QtWidgets.QApplication.quit)
        self.main_window.menuBar.file.actionNewProject.triggered.connect(self._handle_new_project_action)
        self.main_window.menuBar.file.actionOpenProject.triggered.connect(self._handle_open_project_action)
        self.main_window.menuBar.file.actionSaveProject.triggered.connect(self._handle_save_project_action)
        self.main_window.menuBar.file.actionCloseProject.triggered.connect(self._handle_close_project_action)
        self.main_window.menuBar.file.actionImportExcel.triggered.connect(self._handle_import_excel_action)
        self.main_window.menuBar.file.actionImportPointCloud.triggered.connect(self._handle_import_point_cloud)
        self.main_window.menuBar.inversions.actionEdit.triggered.connect(self._handle_inversions_edit_action)
        self.main_window.menuBar.inversions.inversion_selected.connect(self.change_current_inversion)

        self._enable_project_ctrl(False)

    def _init_docks(self):
        """Initializes docks"""
        self.edit_electrodes = QtWidgets.QDockWidget("Electrodes", self)
        self.edit_electrodes.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.edit_electrodes)

        # self.region_panel_dock = QtWidgets.QDockWidget("Regions", self)
        # self.region_panel_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        # self.addDockWidget(Qt.LeftDockWidgetArea, self.region_panel_dock)
        # self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)

        self.mesh_cut_tool_panel_dock = QtWidgets.QDockWidget("Mesh cut tool", self)
        self.mesh_cut_tool_panel_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.mesh_cut_tool_panel_dock)

        self.measurements_dock = QtWidgets.QDockWidget("Measurements", self)
        self.measurements_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.measurements_dock)

    def _enable_project_ctrl(self, enable=True):
        self.main_window.menuBar.inversions.setEnabled(enable)
        self.measurement_view.analyse_measurementButton.setEnabled(enable)
        self.measurement_view.run_invButton.setEnabled(enable)
        self.main_window.menuBar.file.actionCloseProject.setEnabled(enable)
        self.main_window.menuBar.file.actionImportExcel.setEnabled(enable)
        self.main_window.menuBar.file.actionImportPointCloud.setEnabled(enable)

    def _show_current_inversion(self):
        prj_dir = self.genie.cfg.current_project_dir
        if self.genie.project_cfg is not None:
            cur_inv = self.genie.project_cfg.curren_inversion_name
        else:
            cur_inv = ""

        self.main_window.set_current_inversion(cur_inv, prj_dir)

    def _handle_new_project_action(self):
        dlg = NewProjectDialog(self)
        if dlg.exec():
            self._handle_close_project_action()

            # make prj dir
            os.makedirs(dlg.project_dir, exist_ok=True)

            self.genie.cfg.current_project_dir = dlg.project_dir
            self.genie.project_cfg = ProjectConfig()

            # first inversion
            self._add_inversion("inv_1")
            self.genie.project_cfg.curren_inversion_name = self.genie.project_cfg.inversions[0]

            self._handle_import_excel_action()
            self._handle_import_point_cloud()

            self.diagram_view._scene.mesh_cut_tool.from_mesh_cut_tool_param(
                self.genie.current_inversion_cfg.mesh_cut_tool_param)

            self._handle_save_project_action()

            self._enable_project_ctrl(True)
            self._show_current_inversion()

    def _handle_open_project_action(self):
        prj_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Open project", "", QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)
        if not prj_dir:
            return

        self.open_project(prj_dir)

    def open_project(self, prj_dir):
        file_name = os.path.join(prj_dir, GENIE_PROJECT_FILE_NAME)
        try:
            with open(file_name) as fd:
                config = json.load(fd)
        except (FileNotFoundError, IOError):
            QtWidgets.QMessageBox.critical(
                self, 'No project',
                'Directory do not contain project.')
            return

        # check version
        expect_version = ProjectConfig().version
        if config["version"] != expect_version:
            QtWidgets.QMessageBox.critical(
                self, 'Bad project version',
                "Expected project version is {}, but opening project has {}.".format(expect_version, config["version"]))

        self._handle_close_project_action()

        self.genie.cfg.current_project_dir = prj_dir
        self.genie.project_cfg = ProjectConfig.deserialize(config)

        self._update_el_meas()
        self.diagram_view.show_pixmap(self.genie)

        self._load_current_inversion()

        self._enable_project_ctrl(True)
        self._show_current_inversion()

    def _show_3d(self):
        file_name = os.path.join(self.genie.cfg.current_project_dir, "inversions",
                                 self.genie.project_cfg.curren_inversion_name, "resistivity.vtk")
        if os.path.isfile(file_name):
            self.tab_wiget.show_3d(file_name)

    def _handle_save_project_action(self):
        if not self.genie.cfg.current_project_dir or self.genie.project_cfg is None:
            return

        self._save_current_inversion()

        data = self.genie.project_cfg.serialize()
        file_name = os.path.join(self.genie.cfg.current_project_dir, GENIE_PROJECT_FILE_NAME)
        with open(file_name, 'w') as fd:
            json.dump(data, fd, indent=4, sort_keys=True)

        print("project saved")

    def _handle_close_project_action(self):
        self._handle_save_project_action()

        self.genie.cfg.current_project_dir = ""
        self.genie.project_cfg = None

        self._electrode_groups = []
        self._measurements = []

        self._electrode_group_model = ElectrodeGroupModel(self._electrode_groups)
        self.el_group_view.view.setModel(self._electrode_group_model)
        self._measurement_model = MeasurementModel(self._measurements)
        self.measurement_view.view.setModel(self._measurement_model)
        self.diagram_view.hide_pixmap()

        self.tab_wiget.hide_3d()

        self._enable_project_ctrl(False)
        self._show_current_inversion()

    def _add_inversion(self, name):
        self._save_current_inversion()

        self.genie.project_cfg.inversions.append(name)
        self.genie.project_cfg.curren_inversion_name = name
        self.genie.current_inversion_cfg = InversionConfig()

        # create inversion directory
        dir = os.path.join(self.genie.cfg.current_project_dir, "inversions", name)
        os.makedirs(dir, exist_ok=True)

        #self._save_current_inversion()
        self._handle_save_project_action()

        self._show_current_inversion()

    def _copy_inversion(self, name, new_name):
        self._save_current_inversion()

        self.genie.project_cfg.inversions.append(new_name)

        # copy inversion directory
        dir = os.path.join(self.genie.cfg.current_project_dir, "inversions", name)
        new_dir = os.path.join(self.genie.cfg.current_project_dir, "inversions", new_name)
        shutil.copytree(dir, new_dir)

        self.genie.project_cfg.curren_inversion_name = new_name
        self._load_current_inversion()
        self._handle_save_project_action()

        self._show_current_inversion()

    def _remove_inversion(self, name):
        self.genie.project_cfg.inversions.remove(name)

        # remove inversion directory
        dir = os.path.join(self.genie.cfg.current_project_dir, "inversions", name)
        shutil.rmtree(dir, ignore_errors=True)

        if self.genie.project_cfg.inversions:
            self.genie.project_cfg.curren_inversion_name = self.genie.project_cfg.inversions[0]
            self._load_current_inversion()
        else:
            self.genie.project_cfg.curren_inversion_name = ""
            self.genie.current_inversion_cfg = None

        self._handle_save_project_action()

        self._show_current_inversion()

    def _load_current_inversion(self):
        if not self.genie.project_cfg.curren_inversion_name:
            return

        file_name = os.path.join(self.genie.cfg.current_project_dir, "inversions",
                                 self.genie.project_cfg.curren_inversion_name, "inv.conf")
        with open(file_name) as fd:
            config = json.load(fd)

        self.genie.current_inversion_cfg = InversionConfig.deserialize(config)

        self.diagram_view._scene.mesh_cut_tool.from_mesh_cut_tool_param(self.genie.current_inversion_cfg.mesh_cut_tool_param)
        self._measurement_model.checkMeasurements(self.genie.current_inversion_cfg.checked_measurements)
        self.measurement_view.view.reset()

        self._show_3d()
        self._show_current_inversion()

    def _save_current_inversion(self):
        if not self.genie.project_cfg.curren_inversion_name:
            return

        self.genie.current_inversion_cfg.mesh_cut_tool_param = self.diagram_view._scene.mesh_cut_tool.to_mesh_cut_tool_param()
        self.genie.current_inversion_cfg.checked_measurements = [m.number for m in self._measurement_model.checkedMeasurements()]

        dir = os.path.join(self.genie.cfg.current_project_dir, "inversions",
                           self.genie.project_cfg.curren_inversion_name)
        os.makedirs(dir, exist_ok=True)
        file_name = os.path.join(dir, "inv.conf")
        data = self.genie.current_inversion_cfg.serialize()
        with open(file_name, "w") as fd:
            json.dump(data, fd, indent=4, sort_keys=True)

    def change_current_inversion(self, name):
        if self.genie.project_cfg.curren_inversion_name == name:
            return

        self._save_current_inversion()
        self.genie.project_cfg.curren_inversion_name = name
        self._load_current_inversion()

    # def _scene_cut_changed(self):
    #     self.genie.current_inversion_cfg.mesh_cut_tool_param = self.diagram_view._scene.mesh_cut_tool.to_mesh_cut_tool_param()

    def _handle_import_excel_action(self):
        dlg = XlsReaderDialog(self, enable_import=True)
        if dlg.exec():
            mgs = dlg.measurements_groups
            dir = dlg.directory
            cfg = self.genie.project_cfg
            prj_dir = self.genie.cfg.current_project_dir
            meas_dir = os.path.join(prj_dir, "measurements")
            shutil.rmtree(meas_dir, ignore_errors=True)
            os.makedirs(meas_dir)

            # remove items with errors
            mgs = [mg for mg in mgs if not mg.has_error]
            for mg in mgs:
                mg.measurements = [m for m in mg.measurements if not m.has_error]

            cfg.xls_measurement_groups = mgs

            for mg in mgs:
                if not mg.has_error:
                    for m in mg.measurements:
                        if not m.has_error:
                            os.makedirs(os.path.join(meas_dir, m.number), exist_ok=True)
                            shutil.copyfile(os.path.join(dir, m.number, m.file), os.path.join(meas_dir, m.number, m.file))

            self._update_el_meas()

            self._handle_save_project_action()

    def _update_el_meas(self):
        self._electrode_groups = []
        self._measurements = []

        def add_electrode_group(electrode_groups, gallery, wall, height):
            eg = None
            for item in electrode_groups:
                if item.gallery == gallery and item.wall == wall and item.height == height:
                    eg = item
                    break
            if eg is None:
                eg = ElectrodeGroup(gallery=gallery, wall=wall, height=height)
                electrode_groups.append(eg)
            return eg

        def add_electrode(group, id, offset, x, y, z):
            group.electrodes.append(Electrode(id=id, offset=offset, x=x, y=y, z=z))

        cfg = self.genie.project_cfg
        for mg in cfg.xls_measurement_groups:
            if not mg.has_error:
                meas_map = {}
                for e in mg.electrodes:
                    eg = add_electrode_group(self._electrode_groups, e.gallery, e.wall, e.height)
                    add_electrode(eg, e.id, 0, -abs(e.x), -abs(e.y), e.z)

                    meas_map[e.meas_id] = e.id
                for m in mg.measurements:
                    if not m.has_error:
                        meas = Measurement(number=m.number, date=m.date, file=m.file, meas_map=meas_map)
                        meas.load_data(self.genie)
                        self._measurements.append(meas)

        self._electrode_group_model = ElectrodeGroupModel(self._electrode_groups)
        self.el_group_view.view.setModel(self._electrode_group_model)
        self._measurement_model = MeasurementModel(self._measurements)
        self.measurement_view.view.setModel(self._measurement_model)

        self.diagram_view.show_electrodes(self._electrode_groups)

    def _handle_import_point_cloud(self):
        prj_dir = self.genie.cfg.current_project_dir
        dlg = PointCloudReaderDialog(self, enable_import=True, work_dir=prj_dir)
        if dlg.exec():
            f1 = os.path.join(prj_dir, "point_cloud.xyz")
            f1_tmp = os.path.join(prj_dir, "point_cloud.xyz.tmp")
            f2 = os.path.join(prj_dir, "point_cloud_pixmap.png")
            f2_tmp = os.path.join(prj_dir, "point_cloud_pixmap.png.tmp")

            # remove old files
            if os.path.exists(f1):
                os.remove(f1)
            if os.path.exists(f2):
                os.remove(f2)

            # rename files
            os.rename(f1_tmp, f1)
            os.rename(f2_tmp, f2)

            cfg = self.genie.project_cfg
            cfg.point_cloud_origin_x = dlg.origin_x
            cfg.point_cloud_origin_y = dlg.origin_y
            cfg.point_cloud_pixmap_x_min = dlg.pixmap_x_min
            cfg.point_cloud_pixmap_y_min = dlg.pixmap_y_min
            cfg.point_cloud_pixmap_scale = dlg.pixmap_scale

            self.diagram_view.show_pixmap(self.genie)

            self._handle_save_project_action()

    def _handle_inversions_edit_action(self):
        dlg = EditInversionsDialog(self.genie, self)
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

    def _handle_analyse_measurementButton(self):
        index = self.measurement_view.view.currentIndex()
        if index.row() >= 0:
            measurement = self._measurement_model._measurements[index.row()]
            from ui.dialogs.analyse_measurement_dialog import AnalyseMeasurementDlg
            dlg = AnalyseMeasurementDlg(self._electrode_groups, measurement, self.genie, self)
            dlg.exec()
        else:
            QtWidgets.QMessageBox.information(
                self, 'Measurement not selected',
                'Select measurement first.')

    def _handle_run_invButton(self):
        prj_dir = self.genie.cfg.current_project_dir
        cloud_file = os.path.join(prj_dir, "point_cloud.xyz")
        if not os.path.exists(cloud_file):
            QtWidgets.QMessageBox.information(
                self, 'No point cloud',
                'Import point cloud first.')
            return

        if not self.genie.project_cfg.curren_inversion_name:
            QtWidgets.QMessageBox.information(
                self, 'No inversion exist',
                'Create inversion first.')
            return

        measurements = self._measurement_model.checkedMeasurements()
        if measurements:
            from ui.dialogs.run_inv import RunInvDlg
            dlg = RunInvDlg(self._electrode_groups, measurements, self.genie, self)
            dlg.exec()

            self._show_3d()
        else:
            QtWidgets.QMessageBox.information(
                self, 'Measurements not checked',
                'Check measurements first.')

    # def _handle_connect_electrodesButton(self):
    #     sel = self.el_group_view.view.selectedIndexes()
    #     if sel:
    #         eg = self._electrode_groups[sel[0].row()]
    #         self.diagram_view.connect_electrodes(eg)

    # def _handle_generate_meshButton(self):
    #     dlg = GenerateMeshDlg(self.diagram_view._scene.decomposition, self)
    #     dlg.exec()