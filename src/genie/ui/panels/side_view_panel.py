from genie.core.data_types import SideViewToolParam
from .mesh_cut_tool_panel import MeshCutToolPanelEdit

from PyQt5 import QtWidgets, QtCore, QtGui

import numpy as np


TOLERANCE = 1e-12


class SideViewPanel(QtWidgets.QWidget):
    view_changed = QtCore.pyqtSignal()

    def __init__(self, parent, diagram):
        super().__init__(parent)

        self._diagram = diagram
        self.genie = parent.genie
        self.diagram_view = parent.diagram_view

        formLayout = QtWidgets.QFormLayout()

        # origin
        layout = QtWidgets.QHBoxLayout()
        self.origin_x_edit = MeshCutToolPanelEdit(self.editing_finished)
        self.origin_y_edit = MeshCutToolPanelEdit(self.editing_finished)
        layout.addWidget(QtWidgets.QLabel("x:"))
        layout.addWidget(self.origin_x_edit)
        layout.addWidget(QtWidgets.QLabel("y:"))
        layout.addWidget(self.origin_y_edit)
        self.center_origin_button = QtWidgets.QPushButton("+")
        self.center_origin_button.setToolTip("Move origin point to center of area defined\nby points cloud, electrode positions and map.")
        self.center_origin_button.clicked.connect(self.center_origin)
        self.center_origin_button.setMaximumWidth(20)
        layout.addWidget(self.center_origin_button)
        formLayout.addRow("Origin:", layout)

        # dir_vec
        layout = QtWidgets.QHBoxLayout()
        self.dir_vec_x_edit = MeshCutToolPanelEdit(self.editing_finished)
        self.dir_vec_y_edit = MeshCutToolPanelEdit(self.editing_finished)
        layout.addWidget(QtWidgets.QLabel("x:"))
        layout.addWidget(self.dir_vec_x_edit)
        layout.addWidget(QtWidgets.QLabel("y:"))
        layout.addWidget(self.dir_vec_y_edit)
        self.x_button = QtWidgets.QPushButton("X")
        self.x_button.setToolTip("Sets direction vector to X direction.")
        self.x_button.clicked.connect(lambda: self.set_dir(20.0, 0.0))
        self.x_button.setMaximumWidth(20)
        layout.addWidget(self.x_button)
        self.mx_button = QtWidgets.QPushButton("-X")
        self.mx_button.setToolTip("Sets direction vector to -X direction.")
        self.mx_button.clicked.connect(lambda: self.set_dir(-20.0, 0.0))
        self.mx_button.setMaximumWidth(20)
        layout.addWidget(self.mx_button)
        self.y_button = QtWidgets.QPushButton("Y")
        self.y_button.setToolTip("Sets direction vector to Y direction.")
        self.y_button.clicked.connect(lambda: self.set_dir(0.0, 20.0))
        self.y_button.setMaximumWidth(20)
        layout.addWidget(self.y_button)
        self.my_button = QtWidgets.QPushButton("-Y")
        self.my_button.setToolTip("Sets direction vector to -Y direction.")
        self.my_button.clicked.connect(lambda: self.set_dir(0.0, -20.0))
        self.my_button.setMaximumWidth(20)
        layout.addWidget(self.my_button)
        formLayout.addRow("Dir vec:", layout)

        # reset buttons
        layout = QtWidgets.QHBoxLayout()
        self.reset_side_viewButton = QtWidgets.QPushButton("Reset side view")
        self.reset_side_viewButton.clicked.connect(self.reset_side_view)
        layout.addWidget(self.reset_side_viewButton)
        formLayout.addRow(layout)

        self.setLayout(formLayout)
        self.setFixedHeight(self.minimumSizeHint().height())

    def scene_side_view_changed(self):
        side_tool = self._diagram.side_view_tool
        self.origin_x_edit.setText("{:.2f}".format(side_tool.origin[0]))
        self.origin_y_edit.setText("{:.2f}".format(side_tool.origin[1]))
        self.dir_vec_x_edit.setText("{:.2f}".format(side_tool.dir_vec[0]))
        self.dir_vec_y_edit.setText("{:.2f}".format(side_tool.dir_vec[1]))

    def editing_finished(self):
        side_tool = self._diagram.side_view_tool
        side_tool.origin = np.array([float(self.origin_x_edit.text()), float(self.origin_y_edit.text())])
        side_tool.dir_vec = np.array([float(self.dir_vec_x_edit.text()), float(self.dir_vec_y_edit.text())])

        side_tool.update()

        self.diagram_view.side_view._scene.updata_screen_rect

    def center_origin(self):
        p = self._diagram.sceneRect().center()
        self.origin_x_edit.setText("{:.2f}".format(p.x()))
        self.origin_y_edit.setText("{:.2f}".format(p.y()))

        self.editing_finished()

    def reset_side_view(self):
        self.genie.current_inversion_cfg.side_view_tool_param = SideViewToolParam()
        self._diagram.side_view_tool.from_side_view_tool_param(
            self.genie.current_inversion_cfg.side_view_tool_param)
        self.center_origin()

    def set_dir(self, x, y):
        self.dir_vec_x_edit.setText("{:.2f}".format(x))
        self.dir_vec_y_edit.setText("{:.2f}".format(y))

        self.editing_finished()
