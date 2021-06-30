from vtk import vtkUnstructuredGridReader, vtkActor, vtkDataSetMapper
from ..color_maps.default_log10 import lut


class UnstructuredGridActor(vtkActor):
    def __init__(self, filename):
        super(UnstructuredGridActor, self).__init__()
        self.model = vtkUnstructuredGridReader()
        self.model.SetFileName(filename)
        self.model.Update()

        self.mapper = vtkDataSetMapper()
        self.mapper.SetInputConnection(self.model.GetOutputPort())
        self.mapper.ScalarVisibilityOn()
        self.mapper.SetScalarRange(self.scalar_range)
        lut.SetRange(self.scalar_range)
        self.mapper.SetLookupTable(lut)

        self.SetMapper(self.mapper)

    @property
    def scalar_range(self):
        scalar_range = self.model.GetOutput().GetScalarRange()
        return max(scalar_range[0], 0.01), scalar_range[1]
