from PyQt5 import QtWidgets, QtGui, QtCore, QtSvg

from genie.core.config import MapTransform

import sys
import math


class CrossRect(QtWidgets.QGraphicsRectItem):
    def __init__(self, size, move_fun):
        super().__init__(-size, -size, 2 * size, 2 * size)
        self.move_fun = move_fun
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            self.move_fun(self.pos())
        return super().itemChange(change, value)


class Cross:
    def __init__(self, scene, color):
        size = 10
        z = 1

        pen = QtGui.QPen(color, 0.5, QtCore.Qt.SolidLine)
        pen_bold = QtGui.QPen(color, 1.5, QtCore.Qt.SolidLine)

        self._rect = CrossRect(size, self.rect_move_to)
        self._rect.setPen(pen_bold)
        self._rect.setZValue(z)
        self._rect.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        self._rect.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        scene.addItem(self._rect)

        self._line1 = QtWidgets.QGraphicsLineItem(-2 * size, 0, 2 * size, 0)
        self._line1.setPen(pen)
        self._line1.setZValue(z)
        self._line1.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        scene.addItem(self._line1)

        self._line2 = QtWidgets.QGraphicsLineItem(0, -2 * size, 0, 2 * size)
        self._line2.setPen(pen)
        self._line2.setZValue(z)
        self._line2.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        scene.addItem(self._line2)

    def rect_move_to(self, pos):
        self._line1.setPos(pos)
        self._line2.setPos(pos)

    def set_pos(self, x, y):
        self._rect.setPos(x, y)

    def pos(self):
        pos = self._rect.pos()
        return pos.x(), pos.y()


class View(QtWidgets.QGraphicsView):
    def __init__(self):
        super().__init__()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
        else:
            factor = 0.8
        self.scale(factor, factor)


class MapDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, map_file=""):
        super().__init__(parent)
        self._map_file = map_file

        self.map_transform = MapTransform()

        self.setWindowTitle("Map")

        main_layout = QtWidgets.QVBoxLayout()

        scene = QtWidgets.QGraphicsScene()
        self._view = View()
        main_layout.addWidget(self._view)
        self._view.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self._view.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self._view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self._view.setRenderHint(QtGui.QPainter.Antialiasing)
        self._view.setFrameShape(QtWidgets.QFrame.NoFrame)
        self._view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self._view.setScene(scene)

        if self._map_file.lower().endswith(".svg"):
            self._map = QtSvg.QGraphicsSvgItem(self._map_file)
        else:
            pixmap = QtGui.QPixmap(self._map_file)
            self._map = QtWidgets.QGraphicsPixmapItem(pixmap)
        scene.addItem(self._map)
        br = self._map.sceneBoundingRect()
        scene.setSceneRect(br)

        self._point1 = Cross(scene, QtGui.QColor("blue"))
        self._point1.set_pos(br.width() * 0.25, br.height() / 2)

        self._point2 = Cross(scene, QtGui.QColor("red"))
        self._point2.set_pos(br.width() * 0.75, br.height() / 2)

        p1_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("P1:")
        label.setStyleSheet("QLabel { color : blue; }")
        p1_layout.addWidget(label)
        p1_layout.addWidget(QtWidgets.QLabel("x:"))
        self._p1_x_edit = QtWidgets.QLineEdit()
        self._p1_x_edit.setValidator(QtGui.QDoubleValidator())
        self._p1_x_edit.setText("0.0")
        p1_layout.addWidget(self._p1_x_edit)
        p1_layout.addWidget(QtWidgets.QLabel("y:"))
        self._p1_y_edit = QtWidgets.QLineEdit()
        self._p1_y_edit.setValidator(QtGui.QDoubleValidator())
        self._p1_y_edit.setText("0.0")
        p1_layout.addWidget(self._p1_y_edit)
        p1_layout.addStretch(1)
        main_layout.addLayout(p1_layout)

        p2_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("P2:")
        label.setStyleSheet("QLabel { color : red; }")
        p2_layout.addWidget(label)
        p2_layout.addWidget(QtWidgets.QLabel("x:"))
        self._p2_x_edit = QtWidgets.QLineEdit()
        self._p2_x_edit.setValidator(QtGui.QDoubleValidator())
        self._p2_x_edit.setText("1.0")
        p2_layout.addWidget(self._p2_x_edit)
        p2_layout.addWidget(QtWidgets.QLabel("y:"))
        self._p2_y_edit = QtWidgets.QLineEdit()
        self._p2_y_edit.setValidator(QtGui.QDoubleValidator())
        self._p2_y_edit.setText("0.0")
        p2_layout.addWidget(self._p2_y_edit)
        p2_layout.addStretch(1)
        main_layout.addLayout(p2_layout)

        # button box
        self._import_button = QtWidgets.QPushButton("Import")
        self._import_button.clicked.connect(self._handle_import_action)
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        button_box.addButton(self._import_button, QtWidgets.QDialogButtonBox.ActionRole)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

        self.setMinimumSize(500, 400)
        self.resize(1000, 800)

    def _handle_import_action(self):
        # map coordinate
        mp1x, mp1y = self._point1.pos()
        mp2x, mp2y = self._point2.pos()

        # coordinates in edits
        e1x = float(self._p1_x_edit.text())
        e1y = float(self._p1_y_edit.text())
        e2x = float(self._p2_x_edit.text())
        e2y = float(self._p2_y_edit.text())

        mx = mp2x - mp1x
        my = mp2y - mp1y
        ex = e2x - e1x
        ey = e2y - e1y

        mdis = math.hypot(mx, my)
        edis = math.hypot(ex, ey)

        tol = 1e-12
        if mdis < tol or edis < tol:
            msg_box = QtWidgets.QMessageBox(self)
            msg_box.setWindowTitle("Error")
            msg_box.setIcon(QtWidgets.QMessageBox.Critical)
            msg_box.setText("Map coordinates or coordinates in edits are the same.")
            msg_box.exec()
            return

        tr = QtGui.QTransform()
        tr.translate(e1x, e1y)

        s = edis / mdis
        tr.scale(-s, s)

        alpha = math.acos((mx * ex + my * ey) / (mdis * edis))
        d = ex * my - ey * mx
        if d < 0:
            alpha *= -1
        tr.rotateRadians(-alpha)

        tr.translate(-mp1x, -mp1y)

        self.map_transform = MapTransform(m11=tr.m11(), m12=tr.m12(),
                                          m21=tr.m21(), m22=tr.m22(),
                                          dx=tr.dx(), dy=tr.dy())
        print(self.map_transform)

        self.accept()

    def showEvent(self, event):
        self._view.fitInView(self._map, QtCore.Qt.KeepAspectRatio)


if __name__ == '__main__':
    def main():
        app = QtWidgets.QApplication(sys.argv)
        dialog = MapDialog(map_file="genie/res/bukov_situace.svg")
        dialog.show()
        sys.exit(app.exec())

    main()
