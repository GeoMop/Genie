"""
Dialog for generating mesh.
"""

from bgem.geometry.geometry import *
from bgem.polygons.polygons import PolygonDecomposition

import os
import sys
import json
from PyQt5 import QtCore, QtGui, QtWidgets


class GenerateMeshDlg(QtWidgets.QDialog):
    def __init__(self, decomp, parent=None):
        super().__init__(parent)

        self._decomp = decomp

        self._work_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "work_dir")

        self.setWindowTitle("Generate mesh")

        grid = QtWidgets.QGridLayout(self)

        # edit for process output
        self._output_edit = QtWidgets.QTextEdit()
        self._output_edit.setReadOnly(True)
        self._output_edit.setFont(QtGui.QFont("monospace"))
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

        self._par_worDirLineEdit = QtWidgets.QLineEdit(self._work_dir)
        self._parameters_formLayout.addRow("workDir:", self._par_worDirLineEdit)

        self._par_verboseCheckBox = QtWidgets.QCheckBox()
        self._par_verboseCheckBox.setChecked(True)
        self._parameters_formLayout.addRow("verbose:", self._par_verboseCheckBox)

        self._par_bottomLineEdit = QtWidgets.QLineEdit("10.0")
        self._parameters_formLayout.addRow("bottom:", self._par_bottomLineEdit)

        self._par_topLineEdit = QtWidgets.QLineEdit("40.0")
        self._parameters_formLayout.addRow("top:", self._par_topLineEdit)

        self._par_floorLineEdit = QtWidgets.QLineEdit("21.7")
        self._parameters_formLayout.addRow("floor:", self._par_floorLineEdit)

        self._par_ceilingLineEdit = QtWidgets.QLineEdit("24.3")
        self._parameters_formLayout.addRow("ceiling:", self._par_ceilingLineEdit)

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

        self.setMinimumSize(500, 850)
        self.resize(700, 500)

    def _proc_started(self):
        self._start_button.setEnabled(False)
        self._kill_button.setEnabled(True)

        self._set_status("Running")

    def _proc_finished(self):
        self._start_button.setEnabled(True)
        self._kill_button.setEnabled(False)

        self._set_status("Ready")

    def _proc_error(self, error):
        if error == QtCore.QProcess.FailedToStart:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("Error")
            msg_box.setIcon(QtWidgets.QMessageBox.Critical)
            msg_box.setText("Failed to start: {} \nwith arguments: {}".format(self._proc.program(), self._proc.arguments()))
            msg_box.exec()

    def _start(self):
        self._output_edit.clear()

        self._gen_mesh()
        return

        if not self._create_input_files():
            return

        args = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "mesh_gen.py")]
        cmd = sys.executable
        self._proc.setWorkingDirectory(self._work_dir)
        self._proc.start(cmd, args)

    def _set_status(self, status):
        self._status_label.setText("Status: {}".format(status))

    def _read_proc_output(self):
        self._output_edit.moveCursor(QtGui.QTextCursor.End)
        self._output_edit.insertPlainText(str(self._proc.readAllStandardOutput(), encoding='utf-8'))
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
        super().reject()

    def _create_input_files(self):
        conf = {}

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

        os.makedirs(self._work_dir, exist_ok=True)

        # file = os.path.join(self._work_dir, "inv.conf")
        # with open(file, 'w') as fd:
        #     json.dump(conf, fd, indent=4, sort_keys=True)
        #
        # data = ert_prepare.prepare(self._electrode_groups, self._measurements)
        # data.save(os.path.join(self._work_dir, "input.dat"))

        return True

    def _gen_mesh(self):
        # layer geometry object
        lg = LayerGeometry()

        # create interfaces
        top_iface = lg.add_interface(transform_z=(1.0, 0.0), elevation=0.0)
        bot_iface = lg.add_interface(transform_z=(1.0, 0.0), elevation=-1.0)
        #top_iface2 = lg.add_interface(transform_z=(1.0, 0.0), elevation=-1.0)
        #bot_iface2 = lg.add_interface(transform_z=(1.0, 0.0), elevation=-2.0)

        # add region to layer geometry
        reg = lg.add_region(name="region_name", dim=RegionDim.bulk)

        for p in self._decomp.points.values():
            p.attr = None
            #print(p)
        for s in self._decomp.segments.values():
            s.attr = None
        for p in self._decomp.polygons.values():
            print(p.attr)
            if p.attr == 10:
                p.attr = None
            else:
                p.attr = reg

        # add layer to layer geometry
        lg.add_stratum_layer(self._decomp, top_iface, self._decomp, bot_iface)
        #lg.add_stratum_layer(decomp2, top_iface2, decomp2, bot_iface2)

        # generate mesh file
        lg.filename_base = "mesh"
        lg.init()

        lg.construct_brep_geometry()
        lg.make_gmsh_shape_dict()
        lg.distribute_mesh_step()

        lg.call_gmsh(mesh_step=0.0)
        lg.modify_mesh()
