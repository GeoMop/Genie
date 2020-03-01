from xlsreader.xls_parser import parse

from PyQt5 import QtWidgets, QtGui

import sys


class XlsReaderDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("XlsReader")

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
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        button_box.addButton(read_button, QtWidgets.QDialogButtonBox.ActionRole)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

        self.resize(600, 300)

    def _handle_read_action(self):
        if not self._file_edit.text():
            return

        self._log.clear()
        measurements_groups, log = parse(self._file_edit.text())
        if log.items:
            self._log.append(log.to_string())
        else:
            self._log.append("Ok.")

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
