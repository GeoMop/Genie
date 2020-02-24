import electrode_parser

from PyQt5 import QtWidgets, QtGui, QtCore

import os
import shutil
import json


class NewProjectDialog(QtWidgets.QDialog):
    """
    New project dialog.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("New project")

        main_layout = QtWidgets.QVBoxLayout()
        formLayout = QtWidgets.QFormLayout()
        main_layout.addLayout(formLayout)

        # location
        self.location_line_edit = QtWidgets.QLineEdit()
        self.location_line_edit.setText("/home/radek/work/Genie/projects/prj1")
        formLayout.addRow("Location:", self.location_line_edit)

        # xls file
        self.xls_file_line_edit = QtWidgets.QLineEdit()
        self.xls_file_line_edit.setText("/home/radek/work/Genie/src/genie/seznam souřadnic ERT bukov_finale_pb 4.xlsx")
        formLayout.addRow("xls file:", self.xls_file_line_edit)

        # button box
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

        self.resize(600, 300)

    def _handle_create_project_action(self):
        # make prj dir
        prj_dir = self.location_line_edit.text()
        os.makedirs(prj_dir, exist_ok=True)

        # parse .xls, save .prj
        xls_file = self.xls_file_line_edit.text()
        res = electrode_parser.parse(xls_file)
        to_save = {}
        to_save["electrode_groups"] = [eg.serialize() for eg in res["electrode_groups"]]
        to_save["measurements"] = [eg.serialize() for eg in res["measurements"]]
        file = os.path.join(prj_dir, "genie.prj")
        with open(file, 'w') as fd:
            json.dump(to_save, fd, indent=4, sort_keys=True)

        # copy measurements files
        xls_dir = os.path.dirname(xls_file)
        meas_dir = os.path.join(prj_dir, "measurements")
        os.makedirs(meas_dir, exist_ok=True)
        for m in res["measurements"]:
            shutil.copyfile(os.path.join(xls_dir, m.file),
                            os.path.join(meas_dir, m.file))

    def accept(self):
        self._handle_create_project_action()

        super().accept()
