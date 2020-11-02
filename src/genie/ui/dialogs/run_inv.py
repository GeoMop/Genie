"""
Dialog for running inversion.
"""

from genie.core import ert_prepare, st_prepare
from genie.core.data_types import InversionParam, MeshFrom
from genie.core.global_const import GenieMethod

import os
import sys
import json
from PyQt5 import QtCore, QtGui, QtWidgets


class RunInvDlg(QtWidgets.QDialog):
    def __init__(self, electrode_groups, measurements, genie, parent=None):
        super().__init__(parent)

        self._electrode_groups = electrode_groups
        self._measurements = measurements
        self.genie = genie

        #self._work_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "work_dir")
        #self._work_dir = "/home/radek/work/Genie/projects/prj2/inversions/inv_1"
        self._work_dir = os.path.join(parent.genie.cfg.current_project_dir, "inversions",
                                      parent.genie.project_cfg.curren_inversion_name)

        self.setWindowTitle("Run inversion")

        grid = QtWidgets.QGridLayout(self)

        # edit for process output
        self._output_edit = QtWidgets.QTextEdit()
        self._output_edit.setReadOnly(True)
        font = QtGui.QFont("monospace")
        font.setStyleHint(QtGui.QFont.TypeWriter)
        self._output_edit.setFont(font)
        grid.addWidget(self._output_edit, 0, 0, 4, 6)

        # label for showing status
        self._status_label = QtWidgets.QLabel()
        self._set_status("Ready")
        self._status_label.setMaximumHeight(40)
        grid.addWidget(self._status_label, 4, 0, 1, 1)

        # parameters form
        self._parameters_formLayout = QtWidgets.QFormLayout()
        grid.addLayout(self._parameters_formLayout, 5, 0)

        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)

        label = QtWidgets.QLabel("General")
        label.setFont(font)
        self._parameters_formLayout.addRow(label)

        self._par_worDirLabel = QtWidgets.QLabel(self._work_dir)
        self._parameters_formLayout.addRow("workDir:", self._par_worDirLabel)

        self._par_verboseCheckBox = QtWidgets.QCheckBox()
        self._par_verboseCheckBox.setChecked(True)
        self._parameters_formLayout.addRow("verbose:", self._par_verboseCheckBox)

        label = QtWidgets.QLabel("Error")
        label.setFont(font)
        #self._parameters_formLayout.addRow(label)

        self._par_absoluteErrorLineEdit = QtWidgets.QLineEdit("0.001")
        #self._parameters_formLayout.addRow("absoluteError:", self._par_absoluteErrorLineEdit)

        self._par_relativeErrorLineEdit = QtWidgets.QLineEdit("0.03")
        #self._parameters_formLayout.addRow("relativeError:", self._par_relativeErrorLineEdit)

        label = QtWidgets.QLabel("Mesh")
        label.setFont(font)
        self._parameters_formLayout.addRow(label)

        self._par_meshFromComboBox = QtWidgets.QComboBox()
        prj_dir = genie.cfg.current_project_dir
        file = os.path.join(prj_dir, "point_cloud.xyz")
        if os.path.isfile(file):
            self._par_meshFromComboBox.addItem("Gallery cloud", MeshFrom.GALLERY_CLOUD)
            self._par_meshFromComboBox.addItem("Surface cloud", MeshFrom.SURFACE_CLOUD)
        file = os.path.join(prj_dir, "gallery_mesh.msh")
        if os.path.isfile(file):
            self._par_meshFromComboBox.addItem("Gallery mesh", MeshFrom.GALLERY_MESH)
        self._parameters_formLayout.addRow("meshFrom:", self._par_meshFromComboBox)

        self._par_meshFileLineEdit = QtWidgets.QLineEdit("mesh_out.msh")
        #self._parameters_formLayout.addRow("meshFile:", self._par_meshFileLineEdit)

        self._par_reconstructionDepthLineEdit = QtWidgets.QLineEdit("6")
        self._parameters_formLayout.addRow("reconstructionDepth:", self._par_reconstructionDepthLineEdit)

        self._par_edgeLengthLineEdit = QtWidgets.QLineEdit("1.0")
        self._parameters_formLayout.addRow("edgeLength:", self._par_edgeLengthLineEdit)

        self._par_refineMeshCheckBox = QtWidgets.QCheckBox()
        self._par_refineMeshCheckBox.setChecked(True)
        self._parameters_formLayout.addRow("refineMesh:", self._par_refineMeshCheckBox)

        self._par_refineP2CheckBox = QtWidgets.QCheckBox()
        self._par_refineP2CheckBox.setChecked(False)
        self._parameters_formLayout.addRow("refineP2:", self._par_refineP2CheckBox)

        self._par_refineMeshCheckBox.stateChanged.connect(self._handle_refine_checkbox_changed)
        self._handle_refine_checkbox_changed()

        self._par_omitBackgroundCheckBox = QtWidgets.QCheckBox()
        self._par_omitBackgroundCheckBox.setChecked(False)
        #self._parameters_formLayout.addRow("omitBackground:", self._par_omitBackgroundCheckBox)

        self._par_depthLineEdit = QtWidgets.QLineEdit()
        #self._parameters_formLayout.addRow("depth:", self._par_depthLineEdit)

        self._par_qualityLineEdit = QtWidgets.QLineEdit("34.0")
        #self._parameters_formLayout.addRow("quality:", self._par_qualityLineEdit)

        self._par_maxCellAreaLineEdit = QtWidgets.QLineEdit("0.0")
        #self._parameters_formLayout.addRow("maxCellArea:", self._par_maxCellAreaLineEdit)

        self._par_paraDXLineEdit = QtWidgets.QLineEdit("0.3")
        #self._parameters_formLayout.addRow("paraDX:", self._par_paraDXLineEdit)

        if self.genie.method == GenieMethod.ERT:
            text = "Electrodes"
        else:
            text = "Sensors"
        label = QtWidgets.QLabel(text)
        label.setFont(font)
        self._parameters_formLayout.addRow(label)

        self._par_snapDistanceLineEdit = QtWidgets.QLineEdit("1.0")
        self._parameters_formLayout.addRow("snapDistance:", self._par_snapDistanceLineEdit)

        label = QtWidgets.QLabel("Inversion")
        label.setFont(font)
        self._parameters_formLayout.addRow(label)

        self._par_zWeightLineEdit = QtWidgets.QLineEdit("0.7")
        self._parameters_formLayout.addRow("zWeight:", self._par_zWeightLineEdit)

        self._par_lamLineEdit = QtWidgets.QLineEdit("20.0")
        self._parameters_formLayout.addRow("lambda:", self._par_lamLineEdit)

        self._par_optimizeLambdaCheckBox = QtWidgets.QCheckBox()
        self._par_optimizeLambdaCheckBox.setChecked(False)
        self._parameters_formLayout.addRow("optimizeLambda:", self._par_optimizeLambdaCheckBox)

        self._par_maxIterLineEdit = QtWidgets.QLineEdit("20")
        self._parameters_formLayout.addRow("maxIter:", self._par_maxIterLineEdit)

        self._par_robustDataCheckBox = QtWidgets.QCheckBox()
        self._par_robustDataCheckBox.setChecked(False)
        self._parameters_formLayout.addRow("robustData:", self._par_robustDataCheckBox)

        self._par_blockyModelCheckBox = QtWidgets.QCheckBox()
        self._par_blockyModelCheckBox.setChecked(False)
        self._parameters_formLayout.addRow("blockyModel:", self._par_blockyModelCheckBox)

        self._par_recalcJacobianCheckBox = QtWidgets.QCheckBox()
        self._par_recalcJacobianCheckBox.setChecked(True)
        #self._parameters_formLayout.addRow("recalcJacobian:", self._par_recalcJacobianCheckBox)

        label = QtWidgets.QLabel("Output")
        label.setFont(font)
        self._parameters_formLayout.addRow(label)

        self._par_p3dStepLineEdit = QtWidgets.QLineEdit("1.0")
        self._parameters_formLayout.addRow("p3dStep:", self._par_p3dStepLineEdit)

        label = QtWidgets.QLabel("Test options")
        label.setFont(font)
        self._parameters_formLayout.addRow(label)

        self._par_data_logCheckBox = QtWidgets.QCheckBox()
        self._par_data_logCheckBox.setChecked(True)
        self._parameters_formLayout.addRow("data_log:", self._par_data_logCheckBox)

        self._par_k_onesCheckBox = QtWidgets.QCheckBox()
        self._par_k_onesCheckBox.setChecked(False)
        self._parameters_formLayout.addRow("k_ones:", self._par_k_onesCheckBox)

        # process
        self._proc = QtCore.QProcess(self)
        self._proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        self._proc.readyReadStandardOutput.connect(self._read_proc_output)
        self._proc.started.connect(self._proc_started)
        self._proc.finished.connect(self._proc_finished)
        self._proc.error.connect(self._proc_error)

        # buttons
        self._start_button = QtWidgets.QPushButton("Start", self)
        self._start_button.clicked.connect(self._start)
        grid.addWidget(self._start_button, 6, 3)
        self._kill_button = QtWidgets.QPushButton("Kill", self)
        self._kill_button.clicked.connect(self._proc.kill)
        self._kill_button.setEnabled(False)
        grid.addWidget(self._kill_button, 6, 4)
        self._close_button = QtWidgets.QPushButton("Close", self)
        self._close_button.clicked.connect(self.reject)
        grid.addWidget(self._close_button, 6, 5)

        self.setLayout(grid)

        self.setMinimumSize(500, 600)
        self.resize(700, 950)

        self._from_inversion_param(genie.current_inversion_cfg.inversion_param)

        # load log
        file = os.path.join(self._work_dir, "inv_log.txt")
        if os.path.isfile(file):
            with open(file) as fd:
                log = fd.read()
            self._output_edit.clear()
            self._output_edit.insertPlainText(log)
            self._output_edit.moveCursor(QtGui.QTextCursor.Start)

    def _handle_refine_checkbox_changed(self, state=None):
        if self._par_refineMeshCheckBox.isChecked():
            self._par_refineP2CheckBox.setEnabled(True)
        else:
            self._par_refineP2CheckBox.setEnabled(False)

    def _proc_started(self):
        self._start_button.setEnabled(False)
        self._kill_button.setEnabled(True)

        self._set_status("Running")

    def _proc_finished(self):
        self._start_button.setEnabled(True)
        self._kill_button.setEnabled(False)

        self._set_status("Ready")

        # save log
        log = self._output_edit.toPlainText()
        file = os.path.join(self._work_dir, "inv_log.txt")
        with open(file, "w") as fd:
            fd.write(log)

    def _proc_error(self, error):
        if error == QtCore.QProcess.FailedToStart:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("Error")
            msg_box.setIcon(QtWidgets.QMessageBox.Critical)
            msg_box.setText("Failed to start: {} \nwith arguments: {}".format(self._proc.program(), self._proc.arguments()))
            msg_box.exec()

    def _start(self):
        # save inversion config
        self.genie.current_inversion_cfg.inversion_param = self._to_inversion_param()
        self.parent()._save_current_inversion()

        # p3d to big
        if False: # todo: nastavit podminku !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("Confirmation")
            msg_box.setIcon(QtWidgets.QMessageBox.Question)
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Cancel)
            button = QtWidgets.QPushButton('&Start')
            msg_box.addButton(button, QtWidgets.QMessageBox.YesRole)
            msg_box.setDefaultButton(button)
            msg_box.setText("p3d file will be to big, due to small p3dStep parameter, do you want to start anyway?")
            msg_box.exec()

            if msg_box.clickedButton() != button:
                return

        self._output_edit.clear()

        # delete old log file
        file = os.path.join(self._work_dir, "inv_log.txt")
        if os.path.isfile(file):
            os.remove(file)

        # delete old measurements info file
        file = os.path.join(self._work_dir, "measurements_info.json")
        if os.path.isfile(file):
            os.remove(file)

        if not self._create_input_files():
            return

        args = ["-u", os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "invert.py")]
        cmd = sys.executable
        self._proc.setWorkingDirectory(self._work_dir)
        self._proc.start(cmd, args)

    def _set_status(self, status):
        self._status_label.setText("Status: {}".format(status))

    def _read_proc_output(self):
        self._output_edit.moveCursor(QtGui.QTextCursor.End)
        self._output_edit.insertPlainText(str(self._proc.readAllStandardOutput(), encoding='utf-8', errors='replace'))
        self._output_edit.moveCursor(QtGui.QTextCursor.End)

    def reject(self):
        if self._proc.state() == QtCore.QProcess.Running:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("Confirmation")
            msg_box.setIcon(QtWidgets.QMessageBox.Question)
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Cancel)
            button = QtWidgets.QPushButton('&Kill')
            msg_box.addButton(button, QtWidgets.QMessageBox.YesRole)
            msg_box.setDefaultButton(button)
            msg_box.setText("Process running, do you want to kill it?")
            msg_box.exec()

            if msg_box.clickedButton() == button:
                self._proc.kill()
            else:
                return

        # save inversion config
        self.genie.current_inversion_cfg.inversion_param = self._to_inversion_param()
        self.parent()._save_current_inversion()

        super().reject()

    def _to_inversion_param(self):
        param = InversionParam()

        try:
            #self._work_dir = self._par_worDirLineEdit.text()
            param.verbose = self._par_verboseCheckBox.isChecked()

            param.absoluteError = float(self._par_absoluteErrorLineEdit.text())
            param.relativeError = float(self._par_relativeErrorLineEdit.text())

            param.meshFile = self._par_meshFileLineEdit.text()
            param.meshFrom = self._par_meshFromComboBox.currentData()
            d = int(self._par_reconstructionDepthLineEdit.text())
            if d < 4:
                d = 4
            elif d > 10:
                d = 10
            param.reconstructionDepth = d
            param.edgeLength = float(self._par_edgeLengthLineEdit.text())
            param.refineMesh = self._par_refineMeshCheckBox.isChecked()
            param.refineP2 = self._par_refineP2CheckBox.isChecked()
            param.omitBackground = self._par_omitBackgroundCheckBox.isChecked()
            text = self._par_depthLineEdit.text()
            if text != "":
                param.depth = float(text)
            else:
                param.depth = None
            param.quality = float(self._par_qualityLineEdit.text())
            param.maxCellArea = float(self._par_maxCellAreaLineEdit.text())
            param.paraDX = float(self._par_paraDXLineEdit.text())

            param.snapDistance = float(self._par_snapDistanceLineEdit.text())

            param.zWeight = float(self._par_zWeightLineEdit.text())
            param.lam = float(self._par_lamLineEdit.text())
            param.optimizeLambda = self._par_optimizeLambdaCheckBox.isChecked()
            param.maxIter = int(self._par_maxIterLineEdit.text())
            param.robustData = self._par_robustDataCheckBox.isChecked()
            param.blockyModel = self._par_blockyModelCheckBox.isChecked()
            param.recalcJacobian = self._par_recalcJacobianCheckBox.isChecked()

            param.p3dStep = float(self._par_p3dStepLineEdit.text())

            param.data_log = self._par_data_logCheckBox.isChecked()
            param.k_ones = self._par_k_onesCheckBox.isChecked()
        except ValueError as e:
            self._output_edit.setText("ValueError: {0}".format(e))
            # todo: je to dobre?
            return InversionParam()

        return param

    def _from_inversion_param(self, param):
        self._par_verboseCheckBox.setChecked(param.verbose)

        self._par_absoluteErrorLineEdit.setText(str(param.absoluteError))
        self._par_relativeErrorLineEdit.setText(str(param.relativeError))

        self._par_meshFileLineEdit.setText(param.meshFile)
        ind = self._par_meshFromComboBox.findData(param.meshFrom)
        if ind < 0:
            ind = 0
        self._par_meshFromComboBox.setCurrentIndex(ind)
        self._par_reconstructionDepthLineEdit.setText(str(param.reconstructionDepth))
        self._par_edgeLengthLineEdit.setText(str(param.edgeLength))
        self._par_refineMeshCheckBox.setChecked(param.refineMesh)
        self._par_refineP2CheckBox.setChecked(param.refineP2)
        self._par_omitBackgroundCheckBox.setChecked(param.omitBackground)
        if param.depth is not None:
            self._par_depthLineEdit.setText(str(param.depth))
        else:
            self._par_depthLineEdit.setText("")
        self._par_qualityLineEdit.setText(str(param.quality))
        self._par_maxCellAreaLineEdit.setText(str(param.maxCellArea))
        self._par_paraDXLineEdit.setText(str(param.paraDX))

        self._par_snapDistanceLineEdit.setText(str(param.snapDistance))

        self._par_zWeightLineEdit.setText(str(param.zWeight))
        self._par_lamLineEdit.setText(str(param.lam))
        self._par_optimizeLambdaCheckBox.setChecked(param.optimizeLambda)
        self._par_maxIterLineEdit.setText(str(param.maxIter))
        self._par_robustDataCheckBox.setChecked(param.robustData)
        self._par_blockyModelCheckBox.setChecked(param.blockyModel)
        self._par_recalcJacobianCheckBox.setChecked(param.recalcJacobian)

        self._par_p3dStepLineEdit.setText(str(param.p3dStep))

        self._par_data_logCheckBox.setChecked(param.data_log)
        self._par_k_onesCheckBox.setChecked(param.k_ones)

    def _create_input_files(self):
        # conf = {}
        #
        # try:
        #     self._work_dir = self._par_worDirLineEdit.text()
        #     conf['verbose'] = self._par_verboseCheckBox.isChecked()
        #
        #     conf['absoluteError'] = float(self._par_absoluteErrorLineEdit.text())
        #     conf['relativeError'] = float(self._par_relativeErrorLineEdit.text())
        #
        #     conf['meshFile'] = self._par_meshFileLineEdit.text()
        #     conf['refineMesh'] = self._par_refineMeshCheckBox.isChecked()
        #     conf['refineP2'] = self._par_refineP2CheckBox.isChecked()
        #     conf['omitBackground'] = self._par_omitBackgroundCheckBox.isChecked()
        #     text = self._par_depthLineEdit.text()
        #     if text != "":
        #         conf['depth'] = float(text)
        #     else:
        #         conf['depth'] = None
        #     conf['quality'] = float(self._par_qualityLineEdit.text())
        #     conf['maxCellArea'] = float(self._par_maxCellAreaLineEdit.text())
        #     conf['paraDX'] = float(self._par_paraDXLineEdit.text())
        #
        #     conf['zWeight'] = float(self._par_zWeightLineEdit.text())
        #     conf['lam'] = float(self._par_lamLineEdit.text())
        #     conf['maxIter'] = int(self._par_maxIterLineEdit.text())
        #     conf['robustData'] = self._par_robustDataCheckBox.isChecked()
        #     conf['blockyModel'] = self._par_blockyModelCheckBox.isChecked()
        #     conf['recalcJacobian'] = self._par_recalcJacobianCheckBox.isChecked()
        # except ValueError as e:
        #     self._output_edit.setText("ValueError: {0}".format(e))
        #     return False

        #os.makedirs(self._work_dir, exist_ok=True)

        # file = os.path.join(self._work_dir, "inv.conf")
        # with open(file, 'w') as fd:
        #     json.dump(conf, fd, indent=4, sort_keys=True)

        if self.genie.method == GenieMethod.ERT:
            data, meas_info = ert_prepare.prepare(self._electrode_groups, self._measurements)
            data.save(os.path.join(self._work_dir, "input.dat"))
            meas_info_file = os.path.join(self._work_dir, "measurements_info.json")
            with open(meas_info_file, "w") as fd:
                json.dump(meas_info.serialize(), fd, indent=4, sort_keys=True)
        else:
            data = st_prepare.prepare(self._electrode_groups, self._measurements, self.genie.current_inversion_cfg.first_arrivals)
            if data.size() > 0:
                data.save(os.path.join(self._work_dir, "input.dat"))
            else:
                msg_box = QtWidgets.QMessageBox(self)
                msg_box.setWindowTitle("Error")
                msg_box.setIcon(QtWidgets.QMessageBox.Critical)
                msg_box.setText("Failed to start inversion. No measurement with first arrival checked to use.")
                msg_box.exec()
                return False

        return True
