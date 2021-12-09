from vtk import vtkActor, vtkPlane, vtkPlaneSource, vtkPolyDataMapper, vtkImplicitPlaneRepresentation,\
                vtkImplicitPlaneWidget2, vtkCommand


class PlaneWidget(vtkImplicitPlaneWidget2):
    def __init__(self, item_actor, interactor):
        super(PlaneWidget, self).__init__()
        self.interactor = interactor
        self.plane = vtkPlane()
        self.plane.SetOrigin(0, 0, 0)
        self.plane.SetNormal(0, 0, 1)

        def callback(caller, name):
            rep = caller.GetRepresentation()
            rep.GetPlane(self.plane)
            self.interactor.plane_changed.emit(self.plane.GetOrigin(), self.plane.GetNormal())

        self.rep = vtkImplicitPlaneRepresentation()
        self.rep.SetPlaceFactor(1.5)
        self.rep.PlaceWidget(item_actor.GetBounds())
        self.rep.SetNormal(self.plane.GetNormal())
        self.rep.OutlineTranslationOff()
        self.rep.ScaleEnabledOff()
        plane_prop = self.rep.GetPlaneProperty()
        plane_prop.SetOpacity(0.1)
        #self.rep.SetDrawPlane(False)

        self.SetInteractor(interactor)
        self.SetRepresentation(self.rep)
        self.AddObserver(vtkCommand.InteractionEvent, callback)
        self.On()

    def update_origin(self, x, y, z):
        self.rep.SetOrigin(x, y, z)
        self.rep.GetPlane(self.plane)
        self.interactor.plane_changed.emit(self.plane.GetOrigin(), self.plane.GetNormal())
        self.interactor.render_window.Render()

    def update_normal(self, x, y, z):
        self.rep.SetNormal(x, y, z)
        self.rep.GetPlane(self.plane)
        self.interactor.plane_changed.emit(self.plane.GetOrigin(), self.plane.GetNormal())
        self.interactor.render_window.Render()