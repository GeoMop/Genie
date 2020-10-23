from xlsreader.xls_parser import parse_ert, parse_st
from genie.core.global_const import GenieMethod

from PyQt5 import QtWidgets, QtGui

import os


class XlsReaderDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, enable_import=False, method=GenieMethod.ERT):
        super().__init__(parent)
        self._log_text = ""
        self.directory = ""
        self.measurements_groups = []
        self._enable_import = enable_import
        self._method = method

        self.setWindowTitle("XLSReader")

        main_layout = QtWidgets.QVBoxLayout()

        file_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Excel file:")
        file_layout.addWidget(label)
        self._file_edit = QtWidgets.QLineEdit()
        file_layout.addWidget(self._file_edit)
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self._handle_browse_action)
        file_layout.addWidget(browse_button)
        main_layout.addLayout(file_layout)

        self._log = QtWidgets.QTextEdit(self)
        self._log.setReadOnly(True)
        self._log.setFont(QtGui.QFont("monospace"))
        main_layout.addWidget(self._log)

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

    def _handle_read_action(self):
        xls_file = self._file_edit.text()
        if not os.path.isfile(xls_file):
            return

        self._log.clear()
        self.directory = os.path.dirname(xls_file)

        if self._method == GenieMethod.ERT:
            self.measurements_groups, log = parse_ert(xls_file)
        else:
            self.measurements_groups, log = parse_st(xls_file)
        if log.items:
            text = log.to_string()
        else:
            text = "Ok."

        text += "\n\nMeasurements without errors:\n"
        meas_nums = sorted([m.number for mg in self.measurements_groups if not mg.has_error for m in mg.measurements
                            if not m.has_error])
        text += "\n".join(meas_nums) + "\n"

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
        self.accept()

    def _handle_browse_action(self):
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Open excel file", "", "Excel Files (*.xlsx)")
        self._file_edit.setText(file[0])
