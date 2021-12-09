from PyQt5.QtWidgets import QWidget, QHBoxLayout, QDoubleSpinBox, QVBoxLayout, QLabel, QSizePolicy, QCheckBox, \
    QPushButton, QDialog
from PyQt5.QtCore import pyqtSignal, Qt

from genie.ui.dialogs.color_map_editor import ColorMapEditor


class ColorMapPanel(QWidget):
    range_changed = pyqtSignal(float, float)

    def __init__(self, min_value, max_value, genie, lut):
        super(ColorMapPanel, self).__init__()
        self.lut = lut
        self.genie = genie
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        first_line = QHBoxLayout()

        self.step = (max_value - min_value)/15

        layout2 = QHBoxLayout()
        layout2.addWidget(QLabel("min:"))

        self.min = QDoubleSpinBox()
        self.min.setValue(min_value)
        self.min.setDecimals(4)
        self.min.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        layout2.addWidget(self.min)
        first_line.addLayout(layout2)
        self.min.setRange(0.0001, max_value)
        self.min.resize(0, 0)
        self.min.setSingleStep(self.step)

        layout2 = QHBoxLayout()
        layout2.addWidget(QLabel("max:"))

        self.max = QDoubleSpinBox()
        self.max.setValue(max_value)
        self.max.setDecimals(4)
        self.max.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        layout2.addWidget(self.max)
        first_line.addLayout(layout2)
        self.max.setRange(min_value, max_value)
        self.max.resize(0, 0)
        self.max.setSingleStep(self.step)

        self.layout.addLayout(first_line)

        self.scale_from_slice_btn = QPushButton("Min/Max from slice")
        self.layout.addWidget(self.scale_from_slice_btn)

        self.log_lin_checkbox = QCheckBox()
        self.log_lin_checkbox.setChecked(True)
        second_line = QHBoxLayout()
        second_line.addWidget(QLabel("Log10 scale:"))
        second_line.addWidget(self.log_lin_checkbox)

        self.link_vals_cols = QCheckBox()
        self.link_vals_cols.setChecked(False)
        link_tooltip = ("Links colors to values as defined in colormap. \n"
                        "If colormap defines color blue (0,0,255) for value 0.5, \n"
                        "then every value 0.5 will be blue despite defined range.")
        label = QLabel("Link colors to values:")
        label.setToolTip(link_tooltip)
        self.link_vals_cols.setToolTip(link_tooltip)
        second_line.addWidget(label)
        second_line.addWidget(self.link_vals_cols)
        second_line.addStretch()

        self.layout.addLayout(second_line)

        self.change_colors_button = QPushButton("Change colors...")
        self.change_colors_button.clicked.connect(self.open_change_color_dialog)
        self.layout.addWidget(self.change_colors_button)

        self.link_vals_cols.stateChanged.connect(self.disable_log_scale)

        self.max.valueChanged.connect(self.update_min_maximum)
        self.min.valueChanged.connect(self.update_max_minimum)

        self.setFixedHeight(self.minimumSizeHint().height())

    def update_max_minimum(self, new_minimum):
        self.max.setMinimum(new_minimum)
        self.range_changed.emit(self.min.value(), self.max.value())

    def update_min_maximum(self, new_maximum):
        self.min.setMaximum(new_maximum)
        self.range_changed.emit(self.min.value(), self.max.value())

    def open_change_color_dialog(self):
        dlg = ColorMapEditor(self.genie)
        if dlg.exec() == QDialog.Accepted:
            dlg.set_new_lut(self.lut)

    def disable_log_scale(self, state):
        if state:
            self.log_lin_checkbox.setChecked(False)
            self.log_lin_checkbox.setEnabled(False)
            self.log_lin_checkbox.setToolTip("Logarithmic scale is unavailable while colors are linked to values")
        else:
            self.log_lin_checkbox.setEnabled(True)
            self.log_lin_checkbox.setToolTip("")
