from PyQt5.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QComboBox


class VisibilityPanel(QWidget):
    def __init__(self, data_array_names, parent=None):
        super(VisibilityPanel, self).__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.data_selection = QComboBox()
        self.data_selection.addItems(data_array_names)
        layout.addWidget(self.data_selection)

        self.show_model = QCheckBox("Show Model")
        self.show_model.setChecked(False)
        layout.addWidget(self.show_model)

        self.show_plane = QCheckBox("Show Cut Plane")
        self.show_plane.setChecked(True)
        layout.addWidget(self.show_plane)

        self.show_slice = QCheckBox("Show Slice")
        self.show_slice.setChecked(True)
        layout.addWidget(self.show_slice)

        self.show_bounds = QCheckBox("Show Boundaries")
        self.show_bounds.setChecked(True)
        layout.addWidget(self.show_bounds)

        self.show_wireframe = QCheckBox("Show Wireframe")
        self.show_wireframe.setChecked(False)
        layout.addWidget(self.show_wireframe)

        self.setFixedHeight(self.minimumSizeHint().height())
