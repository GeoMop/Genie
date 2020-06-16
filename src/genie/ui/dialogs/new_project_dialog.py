from genie.core.global_const import GENIE_PROJECT_FILE_NAME

from PyQt5 import QtWidgets, QtGui, QtCore

import os


class NewProjectDialog(QtWidgets.QDialog):
    """
    New project dialog.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.project_dir = ""

        self.setWindowTitle("New project")

        main_layout = QtWidgets.QVBoxLayout()
        formLayout = QtWidgets.QFormLayout()
        main_layout.addLayout(formLayout)

        # location
        self.location_line_edit = QtWidgets.QLineEdit()
        self.location_line_edit.setText(os.path.join(os.path.abspath(""), "prj1"))
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self._handle_browse_action)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.location_line_edit)
        layout.addWidget(browse_button)
        formLayout.addRow("Project location:", layout)

        # button box
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

        self.resize(600, 300)

    def _handle_create_project_action(self):
        # check if project already exist
        self.project_dir = self.location_line_edit.text()
        prj_conf_file = os.path.join(self.project_dir, GENIE_PROJECT_FILE_NAME)
        if os.path.isfile(prj_conf_file):
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("Error")
            msg_box.setIcon(QtWidgets.QMessageBox.Critical)
            msg_box.setText("There is a project in this location already.")
            msg_box.exec()
            return False
        return True

    def _handle_browse_action(self):
        prj_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "New project", self.location_line_edit.text(),
            QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)
        if prj_dir:
            self.location_line_edit.setText(prj_dir)

    def accept(self):
        if self._handle_create_project_action():
            super().accept()
