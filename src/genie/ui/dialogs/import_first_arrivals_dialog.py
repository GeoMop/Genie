from PyQt5 import QtWidgets, QtGui, QtCore

from genie.core.global_const import GenieMethod
from genie.core.parse_first_arrival import parse_first_arrival
from genie.core.xls_parser import XlsLog, XlsLogItem, XlsLogLevel

import sys
import os

import numpy as np

class ImportFirstArrivalsDialog(QtWidgets.QDialog):
    def __init__(self, electrode_groups, measurements, genie, parent=None, enable_import=False, method=GenieMethod.ERT):
        super().__init__(parent)
        self._log_text = ""
        self.directory = ""
        self.first_arrivals = []
        self.apply_abs_transform = True
        self._enable_import = enable_import
        self._method = method
        self._electrode_groups = electrode_groups
        self._measurements = measurements
        self.genie = genie

        self.fa_tmp = {}

        self.setWindowTitle("Open first arrivals file")

        main_layout = QtWidgets.QVBoxLayout()

        file_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Excel file:")
        file_layout.addWidget(label)
        self._file_edit = QtWidgets.QLineEdit()
        self._file_edit.returnPressed.connect(self._handle_read_action)
        file_layout.addWidget(self._file_edit)
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self._handle_browse_action)
        file_layout.addWidget(browse_button)
        main_layout.addLayout(file_layout)

        self._log = QtWidgets.QTextEdit(self)
        self._log.setReadOnly(True)
        self._log.setFont(QtGui.QFont("monospace"))
        main_layout.addWidget(self._log)

        self._apply_abs_transform_checkbox = QtWidgets.QCheckBox("Apply transform x = -abs(x), y = -abs(y)")
        self._apply_abs_transform_checkbox.setChecked(True)
        main_layout.addWidget(self._apply_abs_transform_checkbox)

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Tolerance:"))
        self._tolerance_edit = QtWidgets.QLineEdit()
        self._tolerance_edit.setValidator(QtGui.QDoubleValidator())
        self._tolerance_edit.setText("0.1")
        self._tolerance_edit.setToolTip("Tolerance used in finding corresponding sensors. [m]")
        layout.addWidget(self._tolerance_edit)
        layout.addStretch()
        main_layout.addLayout(layout)

        # button box
        read_button = QtWidgets.QPushButton("Read")
        read_button.clicked.connect(self._handle_read_action)
        save_results_button = QtWidgets.QPushButton("Save results...")
        save_results_button.clicked.connect(self._handle_save_results_action)
        self._import_button = QtWidgets.QPushButton("Import")
        self._import_button.clicked.connect(self._handle_import_action)
        self._import_button.setEnabled(False)
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        button_box.addButton(read_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(save_results_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(self._import_button, QtWidgets.QDialogButtonBox.ActionRole)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

        self.resize(600, 300)

    def _find_meas(self):
        tol = float(self._tolerance_edit.text())

        s_ids = [self._find_id(fa.s_x, fa.s_y, fa.s_z, tol) for fa in self.first_arrivals]
        r_ids = [self._find_id(fa.r_x, fa.r_y, fa.r_z, tol) for fa in self.first_arrivals]

        log = XlsLog()

        for i, fa in enumerate(self.first_arrivals):
            found = False
            for ms in self._measurements:
                if s_ids[i] is None or r_ids[i] is None:
                    continue

                if ms.source_id != s_ids[i]:
                    continue

                if ms.receiver_stop >= ms.receiver_start:
                    receivers = list(range(ms.receiver_start, ms.receiver_stop + 1))
                else:
                    receivers = list(range(ms.receiver_start, ms.receiver_stop - 1, -1))

                if r_ids[i] not in receivers:
                    continue

                channel = receivers.index(r_ids[i]) + ms.channel_start - 1

                ind = self._find_fa_ind(ms, channel)
                if ind is not None:
                    self.fa_tmp[ind] = fa.time
                    found = True

            if not found:
                log.add_item(XlsLogItem(XlsLogLevel.WARNING, fa.xls_row, fa.xls_col, "Source and receiver not found in any measurements."))

        return log

    def _find_id(self, x, y, z, tol=0.1):
        if self._apply_abs_transform_checkbox.isChecked():
            p = np.array([-abs(x), -abs(y), z])
        else:
            p = np.array([x, y, z])

        for eg in self._electrode_groups:
            for e in eg.electrodes:
                tp = np.array([e.x, e.y, e.z])
                if np.linalg.norm(tp - p) <= tol:
                    return e.id

        return None

    def _find_fa_ind(self, ms, channel):
        for ind, fa in enumerate(self.genie.current_inversion_cfg.first_arrivals):
            if fa.file == ms.file and fa.channel == channel:
                return ind
        return None

    def _handle_read_action(self):
        xls_file = self._file_edit.text()
        if not os.path.isfile(xls_file):
            return

        self._log.clear()
        self.directory = os.path.dirname(xls_file)

        self.first_arrivals, log = parse_first_arrival(xls_file)

        if log.items:
            text = log.to_string()
        else:
            text = "Reading Ok."

        # remove items with errors
        self.first_arrivals = [fa for fa in self.first_arrivals if not fa.has_error]

        log2 = self._find_meas()

        text += "\n\n"

        if log2.items:
            text += log2.to_string()
        else:
            text += "Finding measurements Ok."

        self._log_text = text
        self._log.append(text)
        self._log.moveCursor(QtGui.QTextCursor.End)

        if self._enable_import:
            self._import_button.setEnabled(True)

    def _handle_save_results_action(self):
        if self._log_text:
            file = QtWidgets.QFileDialog.getSaveFileName(self, "Save results to file",
                                                         os.path.join(self.directory, "results.txt"),
                                                         "Text Files (*.txt)")
            file_name = file[0]
            if file_name:
                with open(file_name, 'w') as fd:
                    fd.write(self._log_text)

    def _handle_import_action(self):
        self.apply_abs_transform = self._apply_abs_transform_checkbox.isChecked()

        self.accept()

    def _handle_browse_action(self):
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Open excel file", "", "Excel Files (*.xlsx)")[0]
        if file:
            self._file_edit.setText(file)

            app = QtWidgets.QApplication.instance()
            app.processEvents(QtCore.QEventLoop.AllEvents, 0)

            self._handle_read_action()

    def keyPressEvent(self, evt):
        if evt.key() == QtCore.Qt.Key_Enter or evt.key() == QtCore.Qt.Key_Return:
            return
        super().keyPressEvent(evt)


if __name__ == '__main__':
    def main():
        app = QtWidgets.QApplication(sys.argv)
        dialog = ImportFirstArrivalsDialog()
        dialog.show()
        sys.exit(app.exec())

    main()
