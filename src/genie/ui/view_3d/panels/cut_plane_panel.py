from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSpinBox, QLabel, QHBoxLayout, QPushButton, QGridLayout
from PyQt5.QtCore import pyqtSignal
from ..point_controller import PointControler
import sys


class CutPlanePanel(QWidget):
    def __init__(self, parent=None):
        super(CutPlanePanel, self).__init__(parent)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(QLabel("Origin:"))
        self.origin = PointControler()
        self.layout.addWidget(self.origin)

        self.layout.addWidget(QLabel("Normal:"))
        self.normal = PointControler(non_zero=True)
        self.layout.addWidget(self.normal)

        layout2 = QGridLayout()
        self.x_normal_btn = QPushButton("X Normal")
        layout2.addWidget(self.x_normal_btn, 0, 0)

        self.y_normal_btn = QPushButton("Y Normal")
        layout2.addWidget(self.y_normal_btn, 0, 1)

        self.z_normal_btn = QPushButton("Z Normal")
        layout2.addWidget(self.z_normal_btn, 0, 2)

        self.camera_normal_btn = QPushButton("Camera Normal")
        layout2.addWidget(self.camera_normal_btn, 1, 1)

        self.layout.addLayout(layout2)

        self.setFixedHeight(self.minimumSizeHint().height())

        self.x_normal_btn.clicked.connect(self.set_x_normal)
        self.y_normal_btn.clicked.connect(self.set_y_normal)
        self.z_normal_btn.clicked.connect(self.set_z_normal)

    def update_plane_info(self, origin, normal):
        self.origin.plain_set_point(*origin)
        self.normal.plain_set_point(*normal)

    def set_x_normal(self):
        self.normal.set_point(1, 0, 0)

    def set_y_normal(self):
        self.normal.set_point(0, 1, 0)

    def set_z_normal(self):
        self.normal.set_point(0, 0, 1)



