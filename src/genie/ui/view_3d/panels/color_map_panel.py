from PyQt5.QtWidgets import QWidget, QHBoxLayout, QDoubleSpinBox, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import pyqtSignal

class ColorMapPanel(QWidget):
    range_changed = pyqtSignal(float, float)
    def __init__(self, min_value, max_value, parent=None):
        super(ColorMapPanel, self).__init__(parent)
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        layout2 = QHBoxLayout()
        layout2.addWidget(QLabel("max:"))

        self.step = (max_value - min_value)/15

        self.max = QDoubleSpinBox()
        self.max.setValue(max_value)
        self.max.setDecimals(2)
        self.max.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        layout2.addWidget(self.max)
        self.layout.addLayout(layout2)
        self.max.setRange(min_value, max_value)
        self.max.resize(0, 0)
        self.max.setSingleStep(self.step)

        layout2 = QHBoxLayout()
        layout2.addWidget(QLabel("min:"))

        self.min = QDoubleSpinBox()
        self.min.setValue(min_value)
        self.min.setDecimals(2)
        self.min.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        layout2.addWidget(self.min)
        self.layout.addLayout(layout2)
        self.min.setRange(0.01, max_value)
        self.min.resize(0, 0)
        self.min.setSingleStep(self.step)

        self.max.valueChanged.connect(self.update_min_maximum)
        self.min.valueChanged.connect(self.update_max_minimum)

        self.setFixedHeight(self.minimumSizeHint().height())


    def update_max_minimum(self, new_minimum):
        self.max.setMinimum(new_minimum)
        self.range_changed.emit(self.min.value(), self.max.value())

    def update_min_maximum(self, new_maximum):
        self.min.setMaximum(new_maximum)
        self.range_changed.emit(self.min.value(), self.max.value())

