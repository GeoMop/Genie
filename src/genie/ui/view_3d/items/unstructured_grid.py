from vtk import vtkUnstructuredGridReader, vtkActor, vtkDataSetMapper


class UnstructuredGridActor(vtkActor):
    def __init__(self, filename, lut):
        super(UnstructuredGridActor, self).__init__()
        self.reader = vtkUnstructuredGridReader()
        self.reader.SetFileName(filename)
        self.reader.ReadAllScalarsOn()
        self.reader.Update()
        self.mapper = vtkDataSetMapper()
        self.mapper.SetInputConnection(self.reader.GetOutputPort())
        self.mapper.ScalarVisibilityOn()
        self.mapper.SetScalarRange(self.scalar_range)
        lut.SetRange(self.scalar_range)
        self.mapper.SetLookupTable(lut)
        self.SetMapper(self.mapper)

    @property
    def scalar_range(self):
        scalar_range = self.reader.GetOutput().GetScalarRange()
        return max(scalar_range[0], 0.01), scalar_range[1]

    @property
    def data_fields_names(self):
        return [self.reader.GetScalarsNameInFile(i) for i in range(self.reader.GetNumberOfScalarsInFile())
                if self.reader.GetScalarsNameInFile(i)[0] != '_']

    def change_data_field(self, field_name):
        self.reader.SetScalarsName(field_name)
        self.reader.Update()
