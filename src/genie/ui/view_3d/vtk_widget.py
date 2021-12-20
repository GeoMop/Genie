from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk import vtkCommand, vtkImplicitPlaneRepresentation, vtkSphereSource, vtkPlane, vtkClipPolyData, \
    vtkPolyDataMapper, vtkActor, vtkProperty, vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor, \
    vtkImplicitPlaneWidget2, vtkUnstructuredGridReader, vtkDataSetMapper, vtkInteractorStyleTrackballCamera, \
    vtkScalarBarActor

from .items.unstructured_grid import UnstructuredGridActor
from .items.plane_widget import PlaneWidget
from .items.cutter_actor import CutterActor
from PyQt5.QtCore import pyqtSignal, Qt, QEvent

from .utility import current_inv_colormap_filename
from ..dialogs.color_map_editor import ColorMapPreset
import numpy as np


class VTKWidget(QVTKRenderWindowInteractor):
    plane_changed = pyqtSignal(tuple, tuple)

    def __init__(self, model_file, lut, genie, cut_plane_panel):
        super(VTKWidget, self).__init__()
        self.cut_plane_panel = cut_plane_panel
        self.genie = genie
        self.lut = lut
        self.model = UnstructuredGridActor(model_file, self.lut)
        self.model.mapper.SetUseLookupTableScalarRange(True)

        self.renderer = vtkRenderer()
        self.renderer.AddActor(self.model)
        self.render_window = self.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.renderer.SetBackground(0.2, 0.2, 0.2)
        self.render_window.Render()
        self.SetInteractorStyle(vtkInteractorStyleTrackballCamera())

        self.scalar_bar = vtkScalarBarActor()
        self.scalar_bar.SetLookupTable(self.lut)
        scalar_bar_width = 0.1
        scalar_bar_height = 0.9
        self.scalar_bar.SetMaximumNumberOfColors(200)
        self.scalar_bar.SetNumberOfLabels(10)
        self.scalar_bar.SetBarRatio(0.2)
        self.scalar_bar.SetWidth(scalar_bar_width)
        self.scalar_bar.SetHeight(scalar_bar_height)
        self.scalar_bar.SetPosition(1 - 0.01 - scalar_bar_width, (1 - scalar_bar_height) / 2)
        self.renderer.AddActor2D(self.scalar_bar)

        self.plane_widget = PlaneWidget(self.model, self)
        self.cut_plane_panel.update_plane_info(self.plane_widget.plane.GetOrigin(),
                                               self.plane_widget.plane.GetNormal())
        self.slice = CutterActor(self.model, self.plane_widget.plane, self.lut)
        self.slice.mapper.SetUseLookupTableScalarRange(True)
        #self.slice.mapper.SetResolveCoincidentTopologyPolygonOffsetParameters(10, 10)
        #self.slice.mapper.SetResolveCoincidentTopologyToPolygonOffset()

        self.renderer.AddObserver("StartEvent", self.correct_cut_plane_depth)
        self.renderer.AddActor(self.slice)
        self.Initialize()
        self.Start()

        self.link_colors_to_values = False

    def correct_cut_plane_depth(self, renderer, event_type):
        self.blockSignals(True)
        camera_normal = np.array(self.renderer.GetActiveCamera().GetViewPlaneNormal())
        plane_normal = self.cut_plane_panel.normal.get_numpy()

        dot_product = camera_normal.dot(plane_normal)
        if dot_product > 0:
            self.plane_widget.plane.SetOrigin(self.cut_plane_panel.origin.get_numpy() + plane_normal * 0.2)
        else:
            self.plane_widget.plane.SetOrigin(self.cut_plane_panel.origin.get_numpy() - plane_normal * 0.2)
        self.blockSignals(False)

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key_I:
            return
        if ev.key() == Qt.Key_W:
            return
        if ev.key() == Qt.Key_S:
            return
        if ev.key() == Qt.Key_P:
            return

        super(VTKWidget, self).keyPressEvent(ev)

    def show_model(self, b):
        #self.plane_widget.rep.SetDrawPlane(b)
        self.model.SetVisibility(b)
        self.render_window.Render()

    def show_plane(self, b):
        self.plane_widget.SetEnabled(b)
        self.render_window.Render()

    def show_bounds(self, b):
        self.plane_widget.rep.SetDrawOutline(b)
        self.render_window.Render()

    def show_slice(self, b):
        self.slice.SetVisibility(b)
        self.render_window.Render()

    def show_wireframe(self, b):
        if b:
            for actor in self.renderer.GetActors():
                actor.GetProperty().SetRepresentationToWireframe()
        else:
            for actor in self.renderer.GetActors():
                actor.GetProperty().SetRepresentationToSurface()
        self.render_window.Render()

    def update_scalar_range(self, min, max):
        if self.link_colors_to_values:
            ColorMapPreset.use_colormap_linked(current_inv_colormap_filename(self.genie),
                                               self.lut,
                                               min,
                                               max)
        else:
            self.lut.SetTableRange(min, max)

        self.render_window.Render()

    def update_range_type(self, state):
        if state == Qt.Checked:
            self.lut.SetScaleToLog10()
        else:
            self.lut.SetScaleToLinear()
        self.render_window.Render()

    def link_state_changed(self, state):
        self.link_colors_to_values = state
        if not state:
            ColorMapPreset.use_colormap(current_inv_colormap_filename(self.genie), self.lut)
        self.update_scalar_range(*self.lut.GetRange())



