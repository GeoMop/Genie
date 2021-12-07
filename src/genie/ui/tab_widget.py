from PyQt5 import QtWidgets
from .tabs.inversion_preparation import InversionPreparation
from .tabs.view_3d import View3D
from .tabs.measurements_model import Measurements_model


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, main_window, genie, parent=None):
        super(TabWidget, self).__init__(parent)
        self.genie = genie

        self._3d_widget = None
        self._meas_model_widget = None

        self.inv_prep = InversionPreparation(main_window, genie, self)
        self.addTab(self.inv_prep, "Inversion Preparation")

    def show_3d(self, model_file):
        self.hide_3d()
        self._3d_widget = View3D(model_file, self.genie)
        self._3d_id = self.addTab(self._3d_widget, "Inversion 3D View")

    def hide_3d(self):
        if self._3d_widget is not None:
            self.removeTab(self.indexOf(self._3d_widget))
            self._3d_widget = None

    def show_meas_model(self, meas_model_file):
        self.hide_meas_model()
        self._meas_model_widget = Measurements_model(meas_model_file)
        self.addTab(self._meas_model_widget, "Measurements on model")

    def hide_meas_model(self):
        if self._meas_model_widget is not None:
            self.removeTab(self.indexOf(self._meas_model_widget))
            self._meas_model_widget = None
