from vtk import vtkLookupTable
from .default_colors import default


lut = vtkLookupTable()
lut.SetNumberOfColors(len(default))
lut.Build()
scalar = 0
for r,g,b in default:
    lut.SetTableValue(scalar, r/256, g/256, b/256, 1.0)
    scalar += 1
lut.SetScaleToLog10()
lut.SetRampToLinear()