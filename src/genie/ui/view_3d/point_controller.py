import numpy as np
from PyQt5.QtWidgets import QWidget, QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QSizePolicy, QApplication, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QDoubleValidator
import sys
class PointControler(QWidget):
    point_changed = pyqtSignal(float, float, float)

    def __init__(self, label=None, non_zero=False, horizontal=True):
        super(PointControler, self).__init__()
        self.non_zero = non_zero
        if horizontal:
            self.layout = QHBoxLayout()
        else:
            self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        if isinstance(label, str):
            self.layout.addWidget(QLabel(label))

        self.x = QLineEdit()
        self.x.setValidator(QDoubleValidator(-sys.float_info.max, sys.float_info.max, 2, self.x))
        self.x.editingFinished.connect(self.on_point_change)
        self.layout.addWidget(self.x)

        self.y = QLineEdit()
        self.y.setValidator(QDoubleValidator(-sys.float_info.max, sys.float_info.max, 2, self.x))
        self.y.editingFinished.connect(self.on_point_change)
        self.layout.addWidget(self.y)

        self.z = QLineEdit()
        self.z.setValidator(QDoubleValidator(-sys.float_info.max, sys.float_info.max, 2, self.x))
        self.z.editingFinished.connect(self.on_point_change)
        self.layout.addWidget(self.z)

        self.layout.addStretch()

        self.msg = QMessageBox(QMessageBox.Warning, "Zero Vector",
                          "This vector should not be zero. \n Update is paused until valid vector is provided.",
                          QMessageBox.Ok, self)

    def get_numpy(self):
        return np.array([float(self.x.text()), float(self.y.text()), float(self.z.text())])

    def on_point_change(self):
        x = float(self.x.text())
        y = float(self.y.text())
        z = float(self.z.text())
        self.x.setText("%.2f" % x)
        self.y.setText("%.2f" % y)
        self.z.setText("%.2f" % z)
        if self.non_zero:
            if x * x + y * y + z * z == 0:

                self.msg.exec()
                return
        self.point_changed.emit(x, y, z)

    def plain_set_point(self, x, y, z):
        self.x.setText("%.2f" % x)
        self.y.setText("%.2f" % y)
        self.z.setText("%.2f" % z)

    def set_point(self, x, y, z):
        self.x.setText("%.2f" % x)
        self.y.setText("%.2f" % y)
        self.z.setText("%.2f" % z)
        self.point_changed.emit(x, y, z)

if __name__ == '__main__':
    app = QApplication(sys.argv)

    mainWindow = PointControler()
    mainWindow.show()
    ret = app.exec()
    sys.exit(ret)