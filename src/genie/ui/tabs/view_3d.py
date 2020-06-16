from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from ..view_3d.vtk_widget import VTKWidget
from ..view_3d.panels.cut_plane_panel import CutPlanePanel
from ..view_3d.panels.visibility_panel import VisibilityPanel
from ..view_3d.panels.color_map_panel import ColorMapPanel


class View3D(QtWidgets.QMainWindow):
    def __init__(self, model_file):
        super(View3D, self).__init__()
        self.init_docks()
        self.vtk_view = VTKWidget(model_file)
        self.vtk_view.update_scalar_range(*self.vtk_view.model.scalar_range)
        self.setCentralWidget(self.vtk_view)

        self.visibility_panel = VisibilityPanel()
        self.visibility_dock.setWidget(self.visibility_panel)

        self.cut_plane_panel = CutPlanePanel()
        self.cut_plane_dock.setWidget(self.cut_plane_panel)
        self.cut_plane_panel.update_plane_info(self.vtk_view.plane_widget.plane.GetOrigin(),
                                               self.vtk_view.plane_widget.plane.GetNormal())

        self.color_map_panel = ColorMapPanel(*self.vtk_view.model.scalar_range)
        self.color_map_dock.setWidget(self.color_map_panel)


        self.resizeDocks([self.cut_plane_dock], [self.cut_plane_panel.minimumSizeHint().width() + 1], Qt.Horizontal)

        self.init_connections()

    def init_docks(self):
        self.cut_plane_dock = QtWidgets.QDockWidget("Cut Plane", self)
        self.cut_plane_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.cut_plane_dock)

        self.color_map_dock = QtWidgets.QDockWidget("Color Map", self)
        self.color_map_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.color_map_dock)

        self.visibility_dock = QtWidgets.QDockWidget("Visibility", self)
        self.visibility_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.visibility_dock)

    def init_connections(self):
        self.visibility_panel.show_model.stateChanged.connect(self.vtk_view.show_model)
        self.visibility_panel.show_slice.stateChanged.connect(self.vtk_view.show_slice)
        self.visibility_panel.show_bounds.stateChanged.connect(self.vtk_view.show_bounds)
        self.visibility_panel.show_plane.stateChanged.connect(self.vtk_view.show_plane)
        self.visibility_panel.show_wireframe.stateChanged.connect(self.vtk_view.show_wireframe)

        self.vtk_view.plane_changed.connect(self.cut_plane_panel.update_plane_info)
        self.cut_plane_panel.origin.point_changed.connect(self.vtk_view.plane_widget.update_origin)
        self.cut_plane_panel.normal.point_changed.connect(self.vtk_view.plane_widget.update_normal)
        self.cut_plane_panel.camera_normal_btn.clicked.connect(self.set_camera_normal)

        self.color_map_panel.range_changed.connect(self.vtk_view.update_scalar_range)

    def set_camera_normal(self):
        self.cut_plane_panel.normal.set_point(*self.vtk_view.renderer.GetActiveCamera().GetViewPlaneNormal())