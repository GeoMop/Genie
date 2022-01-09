from PyQt5 import QtWidgets, QtGui, QtCore

import sys
import os
import shutil


class GalleryMeshDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, enable_import=False, work_dir=""):
        super().__init__(parent)
        self._log_text = ""
        self._enable_import = enable_import
        self._work_dir = work_dir

        self.origin_x = 0.0
        self.origin_y = 0.0
        self.origin_z = 0.0

        self.setWindowTitle("Open gallery mesh file")

        main_layout = QtWidgets.QVBoxLayout()

        file_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Gallery mesh file:")
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

        origin_layout = QtWidgets.QHBoxLayout()
        origin_layout.addWidget(QtWidgets.QLabel("Gallery mesh origin:"))
        origin_layout.addWidget(QtWidgets.QLabel("x:"))
        self._origin_x_edit = QtWidgets.QLineEdit()
        self._origin_x_edit.setValidator(QtGui.QDoubleValidator())
        self._origin_x_edit.setText("-622000.0")
        origin_layout.addWidget(self._origin_x_edit)
        origin_layout.addWidget(QtWidgets.QLabel("y:"))
        self._origin_y_edit = QtWidgets.QLineEdit()
        self._origin_y_edit.setValidator(QtGui.QDoubleValidator())
        self._origin_y_edit.setText("-1128000.0")
        origin_layout.addWidget(self._origin_y_edit)
        origin_layout.addWidget(QtWidgets.QLabel("z:"))
        self._origin_z_edit = QtWidgets.QLineEdit()
        self._origin_z_edit.setValidator(QtGui.QDoubleValidator())
        self._origin_z_edit.setText("0.0")
        origin_layout.addWidget(self._origin_z_edit)
        main_layout.addLayout(origin_layout)

        # button box
        read_button = QtWidgets.QPushButton("Read")
        read_button.clicked.connect(self._handle_read_action)
        save_results_button = QtWidgets.QPushButton("Save results...")
        save_results_button.clicked.connect(self._handle_save_results_action)
        self._import_button = QtWidgets.QPushButton("Import")
        self._import_button.clicked.connect(self._handle_import_action)
        self._import_button.setEnabled(self._enable_import)
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        #button_box.addButton(read_button, QtWidgets.QDialogButtonBox.ActionRole)
        #button_box.addButton(save_results_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(self._import_button, QtWidgets.QDialogButtonBox.ActionRole)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

        self.resize(600, 300)

    def _handle_read_action(self):
        self._log.clear()

        # reading

        self._log_text = self._log.toPlainText()

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
        gallery_mesh_file = self._file_edit.text()
        if not os.path.isfile(gallery_mesh_file):
            return

        out_file = os.path.join(self._work_dir, "gallery_mesh.msh")
        shutil.copyfile(gallery_mesh_file, out_file)

        self.origin_x = float(self._origin_x_edit.text())
        self.origin_y = float(self._origin_y_edit.text())
        self.origin_z = float(self._origin_z_edit.text())

        self.accept()

    def _handle_browse_action(self):
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Open gallery mesh file", "", "Mesh Files (*.msh)")
        self._file_edit.setText(file[0])


if __name__ == '__main__':
    def main():
        app = QtWidgets.QApplication(sys.argv)
        dialog = GalleryMeshDialog()
        dialog.show()
        sys.exit(app.exec())

    main()
