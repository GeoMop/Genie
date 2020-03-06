from xlsreader.xls_parser import parse

from PyQt5 import QtWidgets, QtGui

import sys
import os


class XlsReaderDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._log_text = ""
        self._dir = ""

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
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        button_box.addButton(read_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(save_results_button, QtWidgets.QDialogButtonBox.ActionRole)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

        self.resize(600, 300)

    def _handle_read_action(self):
        xls_file = self._file_edit.text()
        if not os.path.isfile(xls_file):
            return

        self._log.clear()
        self._dir = os.path.dirname(xls_file)

        groups, log = parse(xls_file)
        if log.items:
            text = log.to_string()
        else:
            text = "Ok."

        text += "\n\nMeasurements without errors:\n"
        meas_nums = sorted([m.number for mg in groups if not mg.has_error for m in mg.measurements if not m.has_error])
        text += "\n".join(meas_nums) + "\n"

        self._log_text = text
        self._log.append(text)
        self._log.moveCursor(QtGui.QTextCursor.End)

    def _handle_save_results_action(self):
        if self._log_text:
            file = QtWidgets.QFileDialog.getSaveFileName(self, "Save results to file",
                                                         os.path.join(self._dir, "results.txt"), "Text Files (*.txt)")
            file_name = file[0]
            if file_name:
                with open(file_name, 'w') as fd:
                    fd.write(self._log_text)

    def _handle_browse_action(self):
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Open excel file", "", "Excel Files (*.xlsx)")
        self._file_edit.setText(file[0])


if __name__ == '__main__':
    def main():
        app = QtWidgets.QApplication(sys.argv)
        dialog = XlsReaderDialog()
        dialog.show()
        sys.exit(app.exec())

    main()
