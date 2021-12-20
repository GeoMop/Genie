from vtk import vtkCutter, vtkDataSetMapper, vtkActor, vtkProperty


class CutterActor(vtkActor):
    def __init__(self, item_actor, plane, lut):
        self.cutter = vtkCutter()
        self.cutter.SetCutFunction(plane)
        self.cutter.SetInputConnection(item_actor.reader.GetOutputPort())
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

    @property
    def scalar_range(self):
        scalar_range = self.cutter.GetOutput().GetScalarRange()
        return max(scalar_range[0], 0.01), scalar_range[1]
