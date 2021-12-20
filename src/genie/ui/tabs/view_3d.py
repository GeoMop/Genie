from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from vtkmodules.vtkCommonCore import vtkLookupTable

from ..dialogs.color_map_editor import ColorMapPreset
from ..view_3d.utility import current_inv_colormap_filename
from ..view_3d.vtk_widget import VTKWidget
from ..view_3d.panels.cut_plane_panel import CutPlanePanel
from ..view_3d.panels.visibility_panel import VisibilityPanel
from ..view_3d.panels.color_map_panel import ColorMapPanel


class View3D(QtWidgets.QMainWindow):
    def __init__(self, model_file, genie):
        super(View3D, self).__init__()
        self.lut = vtkLookupTable()
        self.lut.SetScaleToLog10()

        ColorMapPreset.use_colormap(current_inv_colormap_filename(genie), self.lut)

        self.init_docks()
        self.cut_plane_panel = CutPlanePanel()
        self.cut_plane_dock.setWidget(self.cut_plane_panel)

        self.vtk_view = VTKWidget(model_file, self.lut, genie, self.cut_plane_panel)
        self.vtk_view.update_scalar_range(*self.vtk_view.model.scalar_range)
        self.setCentralWidget(self.vtk_view)

        self.visibility_panel = VisibilityPanel(self.vtk_view.model.data_fields_names)
        self.visibility_dock.setWidget(self.visibility_panel)

        self.color_map_panel = ColorMapPanel(*self.vtk_view.model.scalar_range, genie, self.lut)
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
        self.vtk_view.show_model(self.visibility_panel.show_model.checkState())
        self.visibility_panel.show_slice.stateChanged.connect(self.vtk_view.show_slice)
        self.vtk_view.show_slice(self.visibility_panel.show_slice.checkState())
        self.visibility_panel.show_bounds.stateChanged.connect(self.vtk_view.show_bounds)
        self.vtk_view.show_bounds(self.visibility_panel.show_bounds.checkState())
        self.visibility_panel.show_plane.stateChanged.connect(self.vtk_view.show_plane)
        self.vtk_view.show_plane(self.visibility_panel.show_plane.checkState())
        self.visibility_panel.show_wireframe.stateChanged.connect(self.vtk_view.show_wireframe)
        self.vtk_view.show_wireframe(self.visibility_panel.show_wireframe.checkState())
        self.visibility_panel.data_selection.currentTextChanged.connect(self.change_current_data_field)

        self.vtk_view.plane_changed.connect(self.cut_plane_panel.update_plane_info)
        self.cut_plane_panel.origin.point_changed.connect(self.vtk_view.plane_widget.update_origin)
        self.cut_plane_panel.normal.point_changed.connect(self.vtk_view.plane_widget.update_normal)
        self.cut_plane_panel.camera_normal_btn.clicked.connect(self.set_camera_normal)

        self.color_map_panel.range_changed.connect(self.vtk_view.update_scalar_range)
        self.color_map_panel.scale_from_slice_btn.clicked.connect(self.set_scale_from_slice)
        self.color_map_panel.log_lin_checkbox.stateChanged.connect(self.vtk_view.update_range_type)
        self.color_map_panel.link_vals_cols.stateChanged.connect(self.vtk_view.link_state_changed)

        self.vtk_view.render_window.Render()

    def set_camera_normal(self):
        self.cut_plane_panel.normal.set_point(*self.vtk_view.renderer.GetActiveCamera().GetViewPlaneNormal())

    def set_scale_from_slice(self):
        new_range = self.vtk_view.slice.scalar_range
        self.color_map_panel.range_changed.disconnect(self.vtk_view.update_scalar_range)
        self.color_map_panel.min.setValue(new_range[0])
        self.color_map_panel.max.setValue(new_range[1])
        # cannot set minimum higher than maximum or maximum lower than minimum. Second setValue solves it.
        self.color_map_panel.min.setValue(new_range[0])
        self.color_map_panel.max.setValue(new_range[1])
        self.color_map_panel.range_changed.connect(self.vtk_view.update_scalar_range)
        self.vtk_view.update_scalar_range(*new_range)

        self.vtk_view.render_window.Render()

    def change_current_data_field(self, field_name):
        self.vtk_view.model.change_data_field(field_name)
        self.vtk_view.render_window.Render()