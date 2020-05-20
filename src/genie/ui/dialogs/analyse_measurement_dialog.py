"""
Dialog for analysing measurement.
"""

from core import ert_prepare
from core.data_types import InversionParam

import os
import sys
import json
from PyQt5 import QtCore, QtGui, QtWidgets

import pygimli as pg
import numpy as np


class AnalyseMeasurementDlg(QtWidgets.QDialog):
    def __init__(self, electrode_groups, measurement, genie, parent=None):
        super().__init__(parent)

        self._electrode_groups = electrode_groups
        self._measurement = measurement
        self.genie = genie

        self.setWindowTitle("Analyse measurement")

        grid = QtWidgets.QGridLayout(self)

        # edit for output
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
        #self._parameters_formLayout.addRow(label)

        self._par_worDirLineEdit = QtWidgets.QLineEdit("neco")
        self._par_worDirLineEdit.setEnabled(False)
        #self._parameters_formLayout.addRow("workDir:", self._par_worDirLineEdit)

        # buttons
        # self._start_button = QtWidgets.QPushButton("Start", self)
        # self._start_button.setEnabled(False)
        # #self._start_button.clicked.connect(self._start)
        # #grid.addWidget(self._start_button, 6, 3)
        # self._kill_button = QtWidgets.QPushButton("Kill", self)
        # self._kill_button.setEnabled(False)
        # #self._kill_button.clicked.connect(self._proc.kill)
        # self._kill_button.setEnabled(False)
        # #grid.addWidget(self._kill_button, 6, 4)
        self._close_button = QtWidgets.QPushButton("Close", self)
        self._close_button.clicked.connect(self.reject)
        grid.addWidget(self._close_button, 6, 5)

        self.setLayout(grid)

        self.setMinimumSize(500, 850)
        self.resize(1000, 500)

        self._analyse()

    def _analyse(self):
        log = ""
        self._output_edit.clear()

        if self._measurement.data is None:
            return
        d = self._measurement.data["data"]

        data = ert_prepare.prepare(self._electrode_groups, [self._measurement])

        k = pg.geometricFactors(data)

        log += "ca  cb  pa  pb  I         V        std       AppRes AppResGimli ratio ratio2\n"
        log += "----------------------------------------------------------------------------\n"
        print(len(d))
        print(data.size())
        for i in range(data.size()):
            log += "{:3} {:3} {:3} {:3} {:8.6f} {:9.6f} {:6.4f} {:9.2f} {:11.2f} {:5.2f}".format(d["ca"][i], d["cb"][i], d["pa"][i], d["pb"][i], d["I"][i], d["V"][i], d["std"][i], d["AppRes"][i], d["V"][i] / d["I"][i] * k[i], (d["V"][i] / d["I"][i] * k[i])/d["AppRes"][i])
            # if "Electrode distance" in self._measurement.data["header"]:
            #     dis = float(self._measurement.data["header"]["Electrode distance"].split()[0])
            def od(a, b):
                try:
                    return 1.0 / (int(d[b][i]) - int(d[a][i]))
                except:
                    return np.nan

            kk = 1.0 / (od('ca', 'pa') - od('pa', 'cb') - od('ca', 'pb') + od('pb', 'cb')) * 2 * np.pi
            log += " {:6.2f}\n".format((d["V"][i] / d["I"][i] * kk)/d["AppRes"][i])

        self._output_edit.moveCursor(QtGui.QTextCursor.End)
        self._output_edit.insertPlainText(log)
        self._output_edit.moveCursor(QtGui.QTextCursor.Start)

    def _set_status(self, status):
        self._status_label.setText("Status: {}".format(status))
