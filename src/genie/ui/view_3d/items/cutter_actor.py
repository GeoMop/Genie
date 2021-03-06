from vtk import vtkCutter, vtkDataSetMapper, vtkActor, vtkProperty
from ..color_maps.default_log10 import lut


class CutterActor(vtkActor):
    def __init__(self, item_actor, plane):
        self.cutter = vtkCutter()
        self.cutter.SetCutFunction(plane)
        self.cutter.SetInputConnection(item_actor.model.GetOutputPort())
        self.cutter.Update()

        self.mapper = vtkDataSetMapper()
        self.mapper.ScalarVisibilityOn()
        self.mapper.SetLookupTable(lut)
        self.mapper.SetInputConnection(self.cutter.GetOutputPort())

        back = vtkProperty()
        back.SetColor(100, 100, 100)

        self.GetProperty().SetColor(1, 0, 0)
        self.GetProperty().EdgeVisibilityOff()
        self.GetProperty().SetLineWidth(3)
        self.SetMapper(self.mapper)
        self.SetBackfaceProperty(back)
