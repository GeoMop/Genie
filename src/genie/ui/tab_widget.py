from PyQt5 import QtWidgets
from ui.tabs.inversion_preparation import InversionPreparation
from ui.tabs.view_3d import View3D


class TabWidget(QtWidgets.QTabWidget):
    def __init__(self, main_window, genie, parent=None):
        super(TabWidget, self).__init__(parent)

        self._3d_id = None

        self.inv_prep = InversionPreparation(main_window, genie, self)
        self.addTab(self.inv_prep, "Inversion Preparation")

        #self.show_3d("ui/view_3d/dcinv.result.vtk")

    def show_3d(self, model_file):
        self.hide_3d()
        self._3d_id = self.addTab(View3D(model_file), "Inversion 3D View")

    def hide_3d(self):
        if self._3d_id is not None:
            self.removeTab(self._3d_id)
            self._3d_id = None
