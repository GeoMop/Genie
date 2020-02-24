from PyQt5 import QtWidgets, QtGui, QtCore


class EditInversionsDialog(QtWidgets.QDialog):
    """
    Edit inversions dialog.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

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

        self.btnCopy = QtWidgets.QPushButton()
        self.btnCopy.setText("&Copy")
        self.buttonLayout.addWidget(self.btnCopy)

        self.btnDelete = QtWidgets.QPushButton()
        self.btnDelete.setText("&Delete")
        self.buttonLayout.addWidget(self.btnDelete)

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
