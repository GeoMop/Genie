from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk import vtkCommand, vtkImplicitPlaneRepresentation, vtkSphereSource, vtkPlane, vtkClipPolyData, \
    vtkPolyDataMapper, vtkActor, vtkProperty, vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor, \
    vtkImplicitPlaneWidget2, vtkUnstructuredGridReader, vtkDataSetMapper, vtkInteractorStyleTrackballCamera, \
    vtkScalarBarActor
from ui.view_3d.items.unstructured_grid import UnstructuredGridActor
from ui.view_3d.items.plane_widget import PlaneWidget
from ui.view_3d.items.cutter_actor import CutterActor
from PyQt5.QtCore import pyqtSignal, Qt, QEvent
from ui.view_3d.color_maps.default_log10 import lut

class VTKWidget(QVTKRenderWindowInteractor):
    plane_changed = pyqtSignal(tuple, tuple)
    def __init__(self, model_file):
        super(VTKWidget, self).__init__()

        self.model = UnstructuredGridActor(model_file)

        self.renderer = vtkRenderer()
        self.renderer.AddActor(self.model)
        self.render_window = self.GetRenderWindow()
        self.render_window.AddRenderer(self.renderer)
        self.renderer.SetBackground(0.2, 0.2, 0.2)
        self.render_window.Render()
        self.SetInteractorStyle(vtkInteractorStyleTrackballCamera())

        self.scalar_bar = vtkScalarBarActor()
        self.scalar_bar.SetLookupTable(lut)
        scalar_bar_width = 0.1
        scalar_bar_height = 0.9
        self.scalar_bar.SetBarRatio(0.2)
        self.scalar_bar.SetWidth(scalar_bar_width)
        self.scalar_bar.SetHeight(scalar_bar_height)
        self.scalar_bar.SetPosition(1 - 0.01 - scalar_bar_width, (1 - scalar_bar_height) / 2)
        self.renderer.AddActor2D(self.scalar_bar)

        self.plane_widget = PlaneWidget(self.model, self)

        self.slice = CutterActor(self.model, self.plane_widget.plane)
        self.renderer.AddActor(self.slice)
        self.Initialize()
        self.Start()

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
        self.plane_widget.rep.SetDrawPlane(b)
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
                actor.GetProperty().SetRepresentationToWireframe();
        else:
            for actor in self.renderer.GetActors():
                actor.GetProperty().SetRepresentationToSurface();
        self.render_window.Render()

    def update_scalar_range(self, min, max):
        self.model.mapper.SetScalarRange(min, max)
        self.slice.mapper.SetScalarRange(min, max)
        lut.SetTableRange(min, max)
        self.scalar_bar.SetLookupTable(lut)
        self.render_window.Render()
