from PyQt5 import QtWidgets, QtCore, QtGui

import numpy as np


TOLERANCE = 1e-12


class MeshCutToolPanelEdit(QtWidgets.QLineEdit):
    def __init__(self, editing_finished=None):
        super().__init__()
        if editing_finished is not None:
            self.editingFinished.connect(editing_finished)

        self.setValidator(QtGui.QDoubleValidator())


class MeshCutToolPanel(QtWidgets.QWidget):
    cut_changed = QtCore.pyqtSignal()

    def __init__(self, parent, diagram):
        super().__init__(parent)

        self._diagram = diagram

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
        self.center_origin_button.clicked.connect(self.center_origin)
        self.center_origin_button.setMaximumWidth(20)
        layout.addWidget(self.center_origin_button)
        formLayout.addRow("Origin:", layout)

        # gen_vec1
        layout = QtWidgets.QHBoxLayout()
        self.gen_vec1_x_edit = MeshCutToolPanelEdit(self.editing_finished)
        self.gen_vec1_y_edit = MeshCutToolPanelEdit(self.editing_finished)
        layout.addWidget(QtWidgets.QLabel("x:"))
        layout.addWidget(self.gen_vec1_x_edit)
        layout.addWidget(QtWidgets.QLabel("y:"))
        layout.addWidget(self.gen_vec1_y_edit)
        self.gvp1_button = QtWidgets.QPushButton("L")
        self.gvp1_button.clicked.connect(self.qvp1)
        self.gvp1_button.setMaximumWidth(20)
        layout.addWidget(self.gvp1_button)
        formLayout.addRow("Gen vec 1:", layout)

        # gen_vec2
        layout = QtWidgets.QHBoxLayout()
        self.gen_vec2_x_edit = MeshCutToolPanelEdit(self.editing_finished)
        self.gen_vec2_y_edit = MeshCutToolPanelEdit(self.editing_finished)
        layout.addWidget(QtWidgets.QLabel("x:"))
        layout.addWidget(self.gen_vec2_x_edit)
        layout.addWidget(QtWidgets.QLabel("y:"))
        layout.addWidget(self.gen_vec2_y_edit)
        self.gvp2_button = QtWidgets.QPushButton("L")
        self.gvp2_button.clicked.connect(self.qvp2)
        self.gvp2_button.setMaximumWidth(20)
        layout.addWidget(self.gvp2_button)
        formLayout.addRow("Gen vec 2:", layout)

        # z
        layout = QtWidgets.QHBoxLayout()
        self.z_min_edit = MeshCutToolPanelEdit(self.editing_finished)
        self.z_max_edit = MeshCutToolPanelEdit(self.editing_finished)
        layout.addWidget(QtWidgets.QLabel("min:"))
        layout.addWidget(self.z_min_edit)
        layout.addWidget(QtWidgets.QLabel("max:"))
        layout.addWidget(self.z_max_edit)
        formLayout.addRow("Z:", layout)

        # margin
        self.margin_edit = MeshCutToolPanelEdit(self.editing_finished)
        formLayout.addRow("Margin:", self.margin_edit)

        self.setLayout(formLayout)
        self.setFixedHeight(self.minimumSizeHint().height())

    def scene_cut_changed(self):
        cut_tool = self._diagram.mesh_cut_tool
        self.origin_x_edit.setText("{:.2f}".format(cut_tool.origin[0]))
        self.origin_y_edit.setText("{:.2f}".format(cut_tool.origin[1]))
        self.gen_vec1_x_edit.setText("{:.2f}".format(cut_tool.gen_vec1[0]))
        self.gen_vec1_y_edit.setText("{:.2f}".format(cut_tool.gen_vec1[1]))
        self.gen_vec2_x_edit.setText("{:.2f}".format(cut_tool.gen_vec2[0]))
        self.gen_vec2_y_edit.setText("{:.2f}".format(cut_tool.gen_vec2[1]))
        self.z_min_edit.setText("{:.2f}".format(cut_tool.z_min))
        self.z_max_edit.setText("{:.2f}".format(cut_tool.z_max))
        self.margin_edit.setText("{:.2f}".format(cut_tool.margin))

    def editing_finished(self):
        cut_tool = self._diagram.mesh_cut_tool
        cut_tool.origin = np.array([float(self.origin_x_edit.text()), float(self.origin_y_edit.text())])
        cut_tool.gen_vec1 = np.array([float(self.gen_vec1_x_edit.text()), float(self.gen_vec1_y_edit.text())])
        cut_tool.gen_vec2 = np.array([float(self.gen_vec2_x_edit.text()), float(self.gen_vec2_y_edit.text())])
        cut_tool.z_min = float(self.z_min_edit.text())
        cut_tool.z_max = float(self.z_max_edit.text())
        cut_tool.margin = float(self.margin_edit.text())
        cut_tool.update()

    def center_origin(self):
        p = self._diagram.sceneRect().center()
        self.origin_x_edit.setText("{:.2f}".format(p.x()))
        self.origin_y_edit.setText("{:.2f}".format(p.y()))

        self.editing_finished()

    def qvp1(self):
        gen_vec1 = np.array([float(self.gen_vec1_x_edit.text()), float(self.gen_vec1_y_edit.text())])
        gen_vec2 = np.array([float(self.gen_vec2_x_edit.text()), float(self.gen_vec2_y_edit.text())])

        len1 = np.linalg.norm(gen_vec1)
        len2 = np.linalg.norm(gen_vec2)
        if len2 < TOLERANCE:
            return

        ori = gen_vec1[0] * gen_vec2[1] - gen_vec2[0] * gen_vec1[1]
        if ori > 0:
            new = np.array([gen_vec2[1], -gen_vec2[0]])
        else:
            new = np.array([-gen_vec2[1], gen_vec2[0]])

        new = new / len2 * len1

        self.gen_vec1_x_edit.setText("{:.2f}".format(new[0]))
        self.gen_vec1_y_edit.setText("{:.2f}".format(new[1]))

        self.editing_finished()

    def qvp2(self):
        gen_vec1 = np.array([float(self.gen_vec1_x_edit.text()), float(self.gen_vec1_y_edit.text())])
        gen_vec2 = np.array([float(self.gen_vec2_x_edit.text()), float(self.gen_vec2_y_edit.text())])

        len1 = np.linalg.norm(gen_vec1)
        len2 = np.linalg.norm(gen_vec2)
        if len1 < TOLERANCE:
            return

        ori = gen_vec1[0] * gen_vec2[1] - gen_vec2[0] * gen_vec1[1]
        if ori > 0:
            new = np.array([-gen_vec1[1], gen_vec1[0]])
        else:
            new = np.array([gen_vec1[1], -gen_vec1[0]])

        new = new / len1 * len2

        self.gen_vec2_x_edit.setText("{:.2f}".format(new[0]))
        self.gen_vec2_y_edit.setText("{:.2f}".format(new[1]))

        self.editing_finished()
