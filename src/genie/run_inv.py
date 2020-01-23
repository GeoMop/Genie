"""
Dialog for running inversion.
"""

import ert_prepare

import os
import sys
import json
from PyQt5 import QtCore, QtGui, QtWidgets


class RunInvDlg(QtWidgets.QDialog):
    def __init__(self, electrode_groups, measurements, parent=None):
        super().__init__(parent)

        self._electrode_groups = electrode_groups
        self._measurements = measurements

        self._work_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "work_dir")

        self.setWindowTitle("Run inversion")

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

        label = QtWidgets.QLabel("Error")
        label.setFont(font)
        self._parameters_formLayout.addRow(label)

        self._par_absoluteErrorLineEdit = QtWidgets.QLineEdit("0.001")
        self._parameters_formLayout.addRow("absoluteError:", self._par_absoluteErrorLineEdit)

        self._par_relativeErrorLineEdit = QtWidgets.QLineEdit("0.03")
        self._parameters_formLayout.addRow("relativeError:", self._par_relativeErrorLineEdit)

        label = QtWidgets.QLabel("Mesh")
        label.setFont(font)
        self._parameters_formLayout.addRow(label)

        self._par_meshFileLineEdit = QtWidgets.QLineEdit()
        self._parameters_formLayout.addRow("meshFile:", self._par_meshFileLineEdit)

        self._par_refineMeshCheckBox = QtWidgets.QCheckBox()
        self._par_refineMeshCheckBox.setChecked(True)
        self._parameters_formLayout.addRow("refineMesh:", self._par_refineMeshCheckBox)

        self._par_refineP2CheckBox = QtWidgets.QCheckBox()
        self._par_refineP2CheckBox.setChecked(False)
        self._parameters_formLayout.addRow("refineP2:", self._par_refineP2CheckBox)

        self._par_omitBackgroundCheckBox = QtWidgets.QCheckBox()
        self._par_omitBackgroundCheckBox.setChecked(False)
        self._parameters_formLayout.addRow("omitBackground:", self._par_omitBackgroundCheckBox)

        self._par_depthLineEdit = QtWidgets.QLineEdit()
        self._parameters_formLayout.addRow("depth:", self._par_depthLineEdit)

        self._par_qualityLineEdit = QtWidgets.QLineEdit("34.0")
        self._parameters_formLayout.addRow("quality:", self._par_qualityLineEdit)

        self._par_maxCellAreaLineEdit = QtWidgets.QLineEdit("0.0")
        self._parameters_formLayout.addRow("maxCellArea:", self._par_maxCellAreaLineEdit)

        self._par_paraDXLineEdit = QtWidgets.QLineEdit("0.3")
        self._parameters_formLayout.addRow("paraDX:", self._par_paraDXLineEdit)

        label = QtWidgets.QLabel("Inversion")
        label.setFont(font)
        self._parameters_formLayout.addRow(label)

        self._par_zWeightLineEdit = QtWidgets.QLineEdit("0.7")
        self._parameters_formLayout.addRow("zWeight:", self._par_zWeightLineEdit)

        self._par_lamLineEdit = QtWidgets.QLineEdit("20.0")
        self._parameters_formLayout.addRow("lam:", self._par_lamLineEdit)

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
        self._parameters_formLayout.addRow("recalcJacobian:", self._par_recalcJacobianCheckBox)

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

        if not self._create_input_files():
            return

        args = [os.path.join(os.path.dirname(os.path.realpath(__file__)), "invert.py")]
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

        try:
            self._work_dir = self._par_worDirLineEdit.text()
            conf['verbose'] = self._par_verboseCheckBox.isChecked()

            conf['absoluteError'] = float(self._par_absoluteErrorLineEdit.text())
            conf['relativeError'] = float(self._par_relativeErrorLineEdit.text())

            conf['meshFile'] = self._par_meshFileLineEdit.text()
            conf['refineMesh'] = self._par_refineMeshCheckBox.isChecked()
            conf['refineP2'] = self._par_refineP2CheckBox.isChecked()
            conf['omitBackground'] = self._par_omitBackgroundCheckBox.isChecked()
            text = self._par_depthLineEdit.text()
            if text != "":
                conf['depth'] = float(text)
            else:
                conf['depth'] = None
            conf['quality'] = float(self._par_qualityLineEdit.text())
            conf['maxCellArea'] = float(self._par_maxCellAreaLineEdit.text())
            conf['paraDX'] = float(self._par_paraDXLineEdit.text())

            conf['zWeight'] = float(self._par_zWeightLineEdit.text())
            conf['lam'] = float(self._par_lamLineEdit.text())
            conf['maxIter'] = int(self._par_maxIterLineEdit.text())
            conf['robustData'] = self._par_robustDataCheckBox.isChecked()
            conf['blockyModel'] = self._par_blockyModelCheckBox.isChecked()
            conf['recalcJacobian'] = self._par_recalcJacobianCheckBox.isChecked()
        except ValueError as e:
            self._output_edit.setText("ValueError: {0}".format(e))
            return False

        os.makedirs(self._work_dir, exist_ok=True)

        file = os.path.join(self._work_dir, "inv.conf")
        with open(file, 'w') as fd:
            json.dump(conf, fd, indent=4, sort_keys=True)

        data = ert_prepare.prepare(self._electrode_groups, self._measurements)
        data.save(os.path.join(self._work_dir, "input.dat"))

        return True
