import gmsh


model = gmsh.model
factory = model.occ

gmsh.initialize()

gmsh.option.setNumber("General.Terminal", 1)

#gmsh.option.setNumber("Geometry.Tolerance", 0.001)
#gmsh.option.setNumber("Geometry.ToleranceBoolean", 0.001)

model.add("test")

# gmsh.option.setNumber("Mesh.Algorithm", 6)
# gmsh.option.setNumber("Mesh.CharacteristicLengthMin", 0.4)
# gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 0.4)

poly = [(1, 1), (2, 1), (2, 2), (3, 2), (3, 3), (2, 3), (2, 4), (1, 4), (1, 3), (0, 3), (0, 2), (1, 2)]
#poly = [(1, 1), (2, 1), (2, 2), (1, 2)]

box = factory.addBox(-1,0,-1, 5,5,3)

points = []
for p in poly:
    point = factory.addPoint(p[0], p[1], 0)
    points.append(point)

lines = []
for i in range(len(points) - 1):
    line = factory.addLine(points[i], points[i+1])
    lines.append(line)
line = factory.addLine(points[-1], points[0])
lines.append(line)

c = factory.addCurveLoop(lines)
s = factory.addPlaneSurface([c])

g = factory.extrude([(2, s)], 0,0,1)
g = [(dim, tag) for dim, tag in g if dim==3]

factory.cut([(3, box)], g)

factory.synchronize()
model.mesh.generate(3)
gmsh.write("test.msh")

gmsh.finalize()
