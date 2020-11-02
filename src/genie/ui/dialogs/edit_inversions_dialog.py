from PyQt5 import QtWidgets, QtGui, QtCore

import re
import os


class AddInversionDialog(QtWidgets.QDialog):
    re_name = re.compile("^[a-zA-Z0-9]([a-zA-Z0-9]|[_-])*$")

    def __init__(self, parent, genie):
        super().__init__(parent)

        self.genie = genie

        self.inversion_name = ""

        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        form_layout = QtWidgets.QFormLayout()
        self.inversion_line_edit = QtWidgets.QLineEdit()
        form_layout.addRow("Inversion name:", self.inversion_line_edit)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addLayout(form_layout)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)

        self.setWindowTitle('Add inversion')
        self.setMinimumSize(300, 100)

    def accept(self):
        """Handles a confirmation."""
        name = self.inversion_line_edit.text()

        if not self.re_name.match(name):
            QtWidgets.QMessageBox.critical(
                self, 'Name has bad format',
                'Inversion name may contains only letters, digits, "_" and "-".')
            return

        for inv_name in self.genie.project_cfg.inversions:
            if name.lower() == inv_name.lower():
                QtWidgets.QMessageBox.critical(
                    self, 'Name is not unique',
                    "Can't create inversion. The selected inversion name already exists.")
                return

        self.inversion_name = name

        super().accept()


class EditInversionsDialog(QtWidgets.QDialog):
    """
    Edit inversions dialog.
    """
    def __init__(self, genie, parent=None):
        super().__init__(parent)

        self.genie = genie

        self.setWindowTitle("Inversions")

        main_layout = QtWidgets.QVBoxLayout()

        # inversion list tree widget
        self.inversionsListTreeWidget = QtWidgets.QTreeWidget()
        self.inversionsListTreeWidget.setAlternatingRowColors(True)
        self.inversionsListTreeWidget.setHeaderLabels(["Name"])
        self.inversionsListTreeWidget.setSortingEnabled(True)
        self.inversionsListTreeWidget.sortByColumn(0, QtCore.Qt.AscendingOrder)
        main_layout.addWidget(self.inversionsListTreeWidget)

        # buttons
        self.buttonLayout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(self.buttonLayout)

        self.btnAdd = QtWidgets.QPushButton()
        self.btnAdd.setText("&Add")
        self.buttonLayout.addWidget(self.btnAdd)
        self.btnAdd.clicked.connect(self._handle_add_inversion)

        self.btnCopy = QtWidgets.QPushButton()
        self.btnCopy.setText("&Copy")
        self.buttonLayout.addWidget(self.btnCopy)
        self.btnCopy.clicked.connect(self._handle_copy_inversion)

        self.btnDelete = QtWidgets.QPushButton()
        self.btnDelete.setText("&Delete")
        self.buttonLayout.addWidget(self.btnDelete)
        self.btnDelete.clicked.connect(self._handle_delete_inversion)

        spacerItem = QtWidgets.QSpacerItem(20, 40,
                                           QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Minimum)
        self.buttonLayout.addItem(spacerItem)

        self.btnClose = QtWidgets.QPushButton()
        self.btnClose.setText("C&lose")
        self.buttonLayout.addWidget(self.btnClose)
        self.btnClose.clicked.connect(self.reject)

        self.setLayout(main_layout)

        self.resize(600, 500)

        self._inversion_list_reload(self.genie.project_cfg.curren_inversion_name)

    def _inversion_list_reload(self, preferred_inversion=""):
        self.inversionsListTreeWidget.clear()
        to_select = None
        for name in sorted(self.genie.project_cfg.inversions):
            row = QtWidgets.QTreeWidgetItem(self.inversionsListTreeWidget)
            row.setText(0, name)
            if name == preferred_inversion or not to_select:
                to_select = row

        self.inversionsListTreeWidget.resizeColumnToContents(0)

        if to_select:
            self.inversionsListTreeWidget.setCurrentItem(to_select)

    def _handle_add_inversion(self):
        dialog = AddInversionDialog(self, genie=self.genie)
        if dialog.exec():
            self.parent()._add_inversion(dialog.inversion_name)
            self._inversion_list_reload(dialog.inversion_name)

    def _handle_copy_inversion(self):
        currentItem = self.inversionsListTreeWidget.currentItem()
        if currentItem is None:
            return

        dialog = AddInversionDialog(self, genie=self.genie)
        if dialog.exec():
            self.parent()._copy_inversion(currentItem.text(0), dialog.inversion_name)
            self._inversion_list_reload(dialog.inversion_name)

    def _handle_delete_inversion(self):
        currentItem = self.inversionsListTreeWidget.currentItem()
        if currentItem is None:
            return

        msg = QtWidgets.QMessageBox(self)
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setWindowTitle("Delete inversion")
        msg.setText('Are you sure you want to delete "{}" inversion?\n'.format(currentItem.text(0)))
        msg.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
        msg.button(QtWidgets.QMessageBox.Yes).setText("Delete")
        msg.setDefaultButton(QtWidgets.QMessageBox.Yes)
        ret = msg.exec()
        if ret == QtWidgets.QMessageBox.Yes:
            self.parent()._remove_inversion(currentItem.text(0))
            self._inversion_list_reload()
