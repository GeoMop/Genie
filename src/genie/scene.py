#!/usr/bin/env python
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets, QtSvg
from PyQt5.QtCore import Qt
from bgem.external import undo
import mouse
from bgem.polygons.polygons import PolygonDecomposition, enable_undo


enable_undo()


"""
TODO:

- switch buttons
- decomposition:
  wrapper classes: Point, Segment, Polygon (merge with GsPoint etc. add additional info)
  keep both diretion relation to GsPoint, are organized 
  into a dict using same decomp IDs, keep back reference to decomp objects.
   
- move lines with points
- decomposition two modes - with and without intersection tracking, with and without polygons
- add decomposition
"""

class Cursor:
    @classmethod
    def setup_cursors(cls):
        cls.point =  QtGui.QCursor(QtCore.Qt.PointingHandCursor)
        cls.segment = QtGui.QCursor(QtCore.Qt.UpArrowCursor)
        cls.polygon = QtGui.QCursor(QtCore.Qt.CrossCursor)
        cls.draw = QtGui.QCursor(QtCore.Qt.ArrowCursor)

class Region:
    _cols = ["cyan", "magenta", "red", "darkRed", "darkCyan", "darkMagenta",
             "green", "darkBlue", "yellow","blue"]
    colors = [ QtGui.QColor(col) for col in _cols]
    id_next = 1



    def __init__(self, id = None, color = None, name="", dim=0):
        if id is None:
            id = Region.id_next
            Region.id_next += 1
        self.id = id

        if color is None:
            color = Region.colors[self.id%len(Region.colors)].name()
        self.color = color

        self.name = name
        """Region name"""
        self.dim = dim
        """dimension (point = 0, well = 1, fracture = 2, bulk = 3)"""

# Special instances
Region.none = Region(0, "grey", "NONE", -1)



class GsPoint(QtWidgets.QGraphicsEllipseItem):
    SIZE = 6
    STD_ZVALUE = 20
    SELECTED_ZVALUE = 21
    __pen_table={}

    no_brush = QtGui.QBrush(QtCore.Qt.NoBrush)
    no_pen = QtGui.QPen(QtCore.Qt.NoPen)
    add_brush = QtGui.QBrush(QtCore.Qt.darkGreen, QtCore.Qt.SolidPattern)

    @classmethod
    def make_pen(cls, color):
        brush = QtGui.QBrush(color, QtCore.Qt.SolidPattern)
        pen = QtGui.QPen(color, 1.4, QtCore.Qt.SolidLine)
        return (brush, pen)

    @classmethod
    def pen_table(cls, color):
        brush_pen = cls.__pen_table.setdefault(color, cls.make_pen(QtGui.QColor(color)))
        return brush_pen

    def __init__(self, pt):
        self.pt = pt
        #pt.gpt = self
        super().__init__(-self.SIZE, -self.SIZE, 2*self.SIZE, 2*self.SIZE, )
        self.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
            # do not scale points whenzooming
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        #self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
            # Keep point shape (used for mouse interaction) having same size as the point itself.
        #self.setFlag(QtWidgets.QGraphicsItem.ItemClipsToShape, True)
        #self.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)
            # Caching: Points can move.
        # if enabled QGraphicsScene.update() don't repaint

        self.setCursor(Cursor.point)
        self.setAcceptedMouseButtons(QtCore.Qt.LeftButton | QtCore.Qt.RightButton)
        self.update()

    def paint(self, painter, option, widget):
        #print("option: ", option.state)
        #if option.state & QtWidgets.QStyle.State_Selected:
        if self.scene().selection.is_selected(self):
            painter.setBrush(GsPoint.no_brush)
            painter.setPen(self.region_pen)
        else:
            painter.setBrush(self.region_brush)
            painter.setPen(GsPoint.no_pen)
        painter.drawEllipse(self.rect())

    def update(self):
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, False)
        self.setPos(self.pt.xy[0], -self.pt.xy[1])
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)

        color = Region.none.color
        if self.scene():
            regions = self.scene().regions
            key = (1, self.pt.id)
            reg_id = regions.get_shape_region(key)
            color = regions.regions[reg_id].color
        self.region_brush, self.region_pen = GsPoint.pen_table(color)

        self.setZValue(self.STD_ZVALUE)
        super().update()


    def move_to(self, x, y):
        #self.pt.set_xy(x, y)
        displacement = np.array([x - self.pt.xy[0], -y - self.pt.xy[1]])
        if self.scene().decomposition.check_displacment([self.pt], displacement):
            self.scene().decomposition.move_points([self.pt], displacement)

        # for gseg in self.pt.g_segments():
        #     gseg.update()
        if self.scene():
            self.scene().update_all_segments()
            self.scene().update_all_polygons()
        self.update()


    def itemChange(self, change, value):
        """
        The item enables itemChange() notifications for
        ItemPositionChange, ItemPositionHasChanged, ItemMatrixChange,
        ItemTransformChange, ItemTransformHasChanged, ItemRotationChange,
        ItemRotationHasChanged, ItemScaleChange, ItemScaleHasChanged,
        ItemTransformOriginPointChange, and ItemTransformOriginPointHasChanged.
        """
        #print("change: ", change, "val: ", value)
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            #self.pt.set_xy(value.x(), value.y())
            self.move_to(value.x(), value.y())
        if change == QtWidgets.QGraphicsItem.ItemSelectedChange:
            if self.isSelected():
                self.setZValue(self.SELECTED_ZVALUE)
            else:
                self.setZValue(self.STD_ZVALUE)
        return super().itemChange(change, value)


    # def mousePressEvent(self, event):
    #     self.update()
    #     super().mousePressEvent(event)
    #
    # def mouseReleaseEvent(self, event):
    #     self.update()
    #     super().mouseReleaseEvent(event)



class GsSegment(QtWidgets.QGraphicsLineItem):
    __pen_table={}

    WIDTH = 3.0
    STD_ZVALUE = 10
    SELECTED_ZVALUE = 11
    no_pen = QtGui.QPen(QtCore.Qt.NoPen)


    @classmethod
    def make_pen(cls, color):
        pen = QtGui.QPen(color, cls.WIDTH, QtCore.Qt.SolidLine)
        pen.setCosmetic(True)
        selected_pen = QtGui.QPen(color, cls.WIDTH, QtCore.Qt.DashLine)
        selected_pen.setCosmetic(True)
        return (pen, selected_pen)

    @classmethod
    def pen_table(cls, color):
        pens = cls.__pen_table.setdefault(color, cls.make_pen(QtGui.QColor(color)))
        return pens

    def __init__(self, segment):
        self.segment = segment
        #segment.g_segment = self
        super().__init__()
        #self.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        #self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        #self.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)
        # if enabled QGraphicsScene.update() don't repaint

        self.setCursor(Cursor.segment)
        self.setAcceptedMouseButtons(QtCore.Qt.LeftButton | QtCore.Qt.RightButton)
        self.setZValue(self.STD_ZVALUE)
        self.update()

    def update(self):
        #pt_from, pt_to = self.segment.points
        pt_from, pt_to = self.segment.vtxs[0], self.segment.vtxs[1]
        #self.setLine(pt_from.xy[0], pt_from.xy[1], pt_to.xy[0], pt_to.xy[1])
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, False)
        self.setPos(QtCore.QPointF(pt_from.xy[0], -pt_from.xy[1]))
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        self.setLine(0, 0, pt_to.xy[0] - pt_from.xy[0], -pt_to.xy[1] + pt_from.xy[1])

        color = Region.none.color
        if self.scene():
            regions = self.scene().regions
            key = (2, self.segment.id)
            reg_id = regions.get_shape_region(key)
            color = regions.regions[reg_id].color
        self.region_pen, self.region_selected_pen  = GsSegment.pen_table(color)

        super().update()

    def paint(self, painter, option, widget):
        #if option.state & (QtWidgets.QStyle.State_Sunken | QtWidgets.QStyle.State_Selected):
        if self.scene().selection.is_selected(self):
            painter.setPen(self.region_selected_pen)
        else:
            painter.setPen(self.region_pen)
        painter.drawLine(self.line())

    def itemChange(self, change, value):
        #print("change: ", change, "val: ", value)
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            # set new values to data layer
            p0 = self.segment.points[0]
            p1 = self.segment.points[1]
            p0.set_xy(p0.xy[0] + value.x() - self.pos().x(), p0.xy[1] + value.y() - self.pos().y())
            p1.set_xy(p1.xy[0] + value.x() - self.pos().x(), p1.xy[1] + value.y() - self.pos().y())

            # update graphic layer
            p0.gpt.update()
            p1.gpt.update()
            self.scene().update_all_segments()
            self.scene().update_all_polygons()

            return self.pos()
        if change == QtWidgets.QGraphicsItem.ItemSelectedChange:
            if self.isSelected():
                self.setZValue(self.SELECTED_ZVALUE)
            else:
                self.setZValue(self.STD_ZVALUE)
        return super().itemChange(change, value)

    def update_zoom(self, value):
        pen = QtGui.QPen()
        pen.setWidthF(self.WIDTH * 2 / value)
        self.setPen(pen)


class GsPolygon(QtWidgets.QGraphicsPolygonItem):
    __brush_table={}

    SQUARE_SIZE = 20
    STD_ZVALUE = 0
    SELECTED_ZVALUE = 1
    no_pen = QtGui.QPen(QtCore.Qt.NoPen)


    @classmethod
    def make_brush(cls, color):
        brush = QtGui.QBrush(color, QtCore.Qt.SolidPattern)
        return brush

    @classmethod
    def brush_table(cls, color):
        brush = cls.__brush_table.setdefault(color, cls.make_brush(QtGui.QColor(color)))
        return brush

    def __init__(self, polygon):
        self.polygon_data = polygon
        #polygon.g_polygon = self
        self.painter_path = None
        self.depth = 0
        super().__init__()
        #self.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        #self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        #self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges)
        #self.setCacheMode(QtWidgets.QGraphicsItem.DeviceCoordinateCache)
        # if enabled QGraphicsScene.update() don't repaint

        self.setCursor(Cursor.polygon)
        self.setAcceptedMouseButtons(QtCore.Qt.LeftButton | QtCore.Qt.RightButton)
        self.update()

    def update(self):
        points = self.polygon_data.vertices()
        qtpolygon = QtGui.QPolygonF()
        for i in range(len(points)):
            qtpolygon.append(QtCore.QPointF(points[i].xy[0], -points[i].xy[1]))
        qtpolygon.append(QtCore.QPointF(points[0].xy[0], -points[0].xy[1]))

        self.setPolygon(qtpolygon)

        self.painter_path = self._get_polygon_draw_path(self.polygon_data)

        color = Region.none.color
        if self.scene():
            regions = self.scene().regions
            key = (3, self.polygon_data.id)
            reg_id = regions.get_shape_region(key)
            color = regions.regions[reg_id].color
        self.region_brush = GsPolygon.brush_table(color)

        self.depth = self.polygon_data.depth()
        self.setZValue(self.STD_ZVALUE + self.depth)

        super().update()

    def paint(self, painter, option, widget):
        painter.setPen(self.no_pen)
        #if option.state & (QtWidgets.QStyle.State_Sunken | QtWidgets.QStyle.State_Selected):
        if self.scene().selection.is_selected(self):
            brush = QtGui.QBrush(self.region_brush)
            brush.setStyle(QtCore.Qt.Dense4Pattern)
            tr = painter.worldTransform()
            brush.setTransform(QtGui.QTransform.fromScale(self.SQUARE_SIZE / tr.m11(), self.SQUARE_SIZE / tr.m22()))
            painter.setBrush(brush)
        else:
            painter.setBrush(self.region_brush)
        painter.drawPath(self.painter_path)

    def itemChange(self, change, value):
        #print("change: ", change, "val: ", value)
        #if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
        #    self.pt.set_xy(value.x(), value.y())
        # if change == QtWidgets.QGraphicsItem.ItemSelectedChange:
        #     if self.isSelected():
        #         self.setZValue(self.SELECTED_ZVALUE)
        #     else:
        #         self.setZValue(self.STD_ZVALUE)
        return super().itemChange(change, value)

    @staticmethod
    def _get_wire_oriented_vertices(wire):
        """
        Follow the wire segments and get the list of its vertices duplicating the first/last point.
        return: array, shape: n_vtx, 2
        """
        seggen = wire.segments()
        vtxs = []
        for seg, side in seggen:
            # Side corresponds to the end point of the segment. (Indicating also on which side thenwire lies.)
            if not vtxs:
                # first segment - add both vertices, so the loop is closed at the end.
                other_side = not side
                vtxs.append(seg.vtxs[other_side].xy)
            vtxs.append(seg.vtxs[side].xy)
        return np.array(vtxs)

    @classmethod
    def _add_to_painter_path(cls, path, wire):
        vtxs = cls._get_wire_oriented_vertices(wire)
        point_list = [QtCore.QPointF(vtxx, -vtxy) for vtxx, vtxy in vtxs]
        sub_poly = QtGui.QPolygonF(point_list)
        path.addPolygon(sub_poly)

    def _get_polygon_draw_path(self, polygon):
        """Get the path to draw the polygon in, i.e. the outer boundary and inner boundaries.
        The path approach allows holes in polygons and therefore flat depth for polygons (Odd-even paint rule)"""
        complex_path = QtGui.QPainterPath()
        self._add_to_painter_path(complex_path, polygon.outer_wire)
        # Subtract all inner parts
        for inner_wire in polygon.outer_wire.childs:
            self._add_to_painter_path(complex_path, inner_wire)
        return complex_path


class Selection():
    def __init__(self, diagram):
        self._diagram = diagram
        self._selected = []

    def select_item(self, item):
        self._selected.clear()
        self.select_add_item(item)
        self._diagram.update()

        self._diagram.selection_changed.emit()

    def select_add_item(self, item):
        if item in self._selected:
            self._selected.remove(item)
        else:
            self._selected.append(item)
        self._diagram.update()

        self._diagram.selection_changed.emit()

    def select_all(self):
        self._selected.clear()
        self._selected.extend(self._diagram.points.values())
        self._selected.extend(self._diagram.segments.values())
        self._selected.extend(self._diagram.polygons.values())
        self._diagram.update()

        self._diagram.selection_changed.emit()

    def deselect_all(self, emit=True):
        self._selected.clear()
        self._diagram.update()

        if emit:
            self._diagram.selection_changed.emit()

    def is_selected(self, item):
        return item in self._selected


class Regions:
    def __init__(self, diagram):
        self.regions = {Region.none.id: Region.none}
        self._diagram = diagram

    def add_region(self, color=None, name="", dim=0):
        reg = Region(id=None, color=color, name=name, dim=dim)
        self.regions[reg.id] = reg
        return reg.id

    def delete_region(self, id):
        del self.regions[id]

    def get_region_names(self):
        return [reg.name for reg in self.regions.values()]

    def get_shape_region(self, shape_key):
        dim, shape_id = shape_key
        attr = None
        if dim == 1:
            attr = self._diagram.decomposition.points[shape_id].attr
        elif dim == 2:
            attr = self._diagram.decomposition.segments[shape_id].attr
        elif dim == 3:
            attr = self._diagram.decomposition.polygons[shape_id].attr

        if attr is None:
            attr = Region.none.id

        return attr

    def get_common_region(self):
        selected = self._diagram.selection._selected
        r_id = Region.none.id
        if selected:
            r_id = self.get_shape_region(self._diagram.get_shape_key(selected[0]))
            for item in selected[1:]:
                if self.get_shape_region(self._diagram.get_shape_key(item)) != r_id:
                    r_id = Region.none.id
        return r_id

    def set_region(self, dim, shape_id, reg_id):
        if dim != self.regions[reg_id].dim:
            return False

        if reg_id is None:
            reg_id = Region.none.id

        if dim == 1:
            self._diagram.decomposition.points[shape_id].attr = reg_id
        elif dim == 2:
            self._diagram.decomposition.segments[shape_id].attr = reg_id
        elif dim == 3:
            self._diagram.decomposition.polygons[shape_id].attr = reg_id

        return True

    def is_region_used(self, reg_id):
        dim = self.regions[reg_id].dim
        elements = []
        if dim == 1:
            elements = self._diagram.decomposition.points.values()
        elif dim == 2:
            elements = self._diagram.decomposition.segments.values()
        elif dim == 3:
            elements = self._diagram.decomposition.polygons.values()

        for el in elements:
            if reg_id == el.attr:
                return True

        return False


class Diagram(QtWidgets.QGraphicsScene):
    selection_changed = QtCore.pyqtSignal()
    # selection has changed

    def __init__(self, parent):
        rect = QtCore.QRectF(-622500, 1128600, 400, 500)
        super().__init__(rect, parent)
        self.points = {}
        self.segments = {}
        self.polygons = {}

        self.regions = Regions(self)

        self.last_point = None
        self.aux_pt, self.aux_seg = self.create_aux_segment()
        self.hide_aux_line()

        self._zoom_value = 1.0
        self.selection = Selection(self)
        self._press_screen_pos = QtCore.QPoint()

        # polygons
        self.decomposition = PolygonDecomposition()
        res = self.decomposition.get_last_polygon_changes()
        #assert res[0] == PolygonChange.add
        self.outer_id = res[1]
        """Decomposition of the a plane into polygons."""

    def create_aux_segment(self):
        pt_size = GsPoint.SIZE
        no_pen = QtGui.QPen(QtCore.Qt.NoPen)
        add_brush = QtGui.QBrush(QtCore.Qt.darkGreen, QtCore.Qt.SolidPattern)
        pt = self.addEllipse(-pt_size, -pt_size, 2*pt_size, 2*pt_size, no_pen, add_brush)
        pt.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        pt.setCursor(Cursor.draw)
        pt.setZValue(100)
        add_pen = QtGui.QPen(QtGui.QColor(QtCore.Qt.darkGreen), GsSegment.WIDTH)
        add_pen.setCosmetic(True)
        line = self.addLine(0,0,0,0, add_pen)
        line.setZValue(100)
        return pt, line

    def move_aux_segment(self, tip, origin=None):
        """
        Update tip point and show aux segment and point.
        :param tip: Tip point (QPointF)
        :param origin: Origin point (QPointF)
        """
        self.aux_pt.show()
        self.aux_seg.show()
        self.aux_pt.setPos(tip)
        if origin is None:
            origin = self.aux_seg.line().p1()
        self.aux_seg.setLine(QtCore.QLineF(origin, tip))

    def hide_aux_line(self):
        self.aux_pt.hide()
        self.aux_seg.hide()



    def add_point(self, pos, gitem):
        if type(gitem) == GsPoint:
            return gitem
        else:
            #if type(gitem) == GsSegment:
            #pt = Point(pos.x(), pos.y(), Region.none)
            #pt = self.decomposition.add_free_point(None, (pos.x(), -pos.y()), self.outer_id)
            pt = self.decomposition.add_point((pos.x(), -pos.y()))
            if pt.id in self.points:
                gpt = self.points[pt.id]
            else:
                gpt = GsPoint(pt)
                #self.points.append(pt)
                self.points[pt.id] = gpt
                self.addItem(gpt)
            return gpt

    def add_segment(self, gpt1, gpt2):
        #seg = Segment(gpt1.pt, gpt2.pt, Region.none)
        #seg = self.decomposition.new_segment(gpt1.pt, gpt2.pt)
        seg_list = self.decomposition.add_line_for_points(gpt1.pt, gpt2.pt)
        # for seg in seg_list:
        #     gseg = GsSegment(seg)
        #     gseg.update_zoom(self._zoom_value)
        #     self.segments.append(seg)
        #     self.addItem(gseg)
        self.update_scene()

    def new_point(self, pos, gitem, close = False):
        #print("below: ", gitem)
        new_g_point = self.add_point(pos, gitem)
        if self.last_point is not None:
            self.add_segment(self.last_point, new_g_point)
        if not close:
            self.last_point = new_g_point
            pt = new_g_point.pos()
            self.move_aux_segment(pt, origin=pt)
        else:
            self.last_point = None
            self.hide_aux_line()

    def mouse_create_event(self, event):
        #transform = self.parent().transform()
        #below_item = self.itemAt(event.scenePos(), transform)
        below_item = self.below_item(event.scenePos())
        close = event.modifiers() & mouse.Event.Ctrl
        self.new_point(event.scenePos(), below_item, close)
        event.accept()

        self.selection._selected.clear()
        self.update_scene()

    def below_item(self, scene_pos):
        below_item = None
        for item in self.items(scene_pos, deviceTransform=self.parent().transform()):
            if (item is self.aux_pt) or (item is self.aux_seg):
                continue
            below_item = item
            break
        return below_item

    def update_zoom(self, value):
        self._zoom_value = value

        for g_seg in self.segments.values():
            g_seg.update_zoom(value)

    def update_all_segments(self):
        for g_seg in self.segments.values():
            g_seg.update()

    def update_all_polygons(self):
        for g_pol in self.polygons.values():
            g_pol.update()

    def mousePressEvent(self, event):
        """
        :param event: QGraphicsSceneMouseEvent
        :return:
        """
        #print("P last: ", event.lastScenePos())
        # if event.button() == mouse.Event.Right and self.last_point is None:
        #     self.mouse_create_event(event)

        self._press_screen_pos = event.screenPos()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """
        :param event: QGraphicsSceneMouseEvent
        :return:
        """
        #print("R last: ", event.lastScenePos())
        below_item = self.below_item(event.scenePos())
        screen_pos_not_changed = event.screenPos() == self._press_screen_pos

        if event.button() == mouse.Event.Left and screen_pos_not_changed:
            self.mouse_create_event(event)

        if event.button() == mouse.Event.Right and screen_pos_not_changed:
            item = None
            if below_item is not None:
                if type(below_item) is GsPoint:
                    item = below_item
                elif type(below_item) is GsSegment:
                    item = below_item
                elif type(below_item) is GsPolygon:
                    item = below_item

            if event.modifiers() & mouse.Event.Shift:
                if item is not None:
                    self.selection.select_add_item(item)
            else:
                if item is not None:
                    self.selection.select_item(item)
                else:
                    self.selection.deselect_all()

        super().mouseReleaseEvent(event)


    def mouseMoveEvent(self, event):
        if self.last_point is not None:
            self.move_aux_segment(event.scenePos())
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        """Standart key press event"""
        if event.key() == QtCore.Qt.Key_Escape:
            self.last_point = None
            self.hide_aux_line()
        elif event.key() == QtCore.Qt.Key_Delete:
            self.delete_selected()
        elif event.key() == QtCore.Qt.Key_A and event.modifiers() & mouse.Event.Ctrl:
            self.selection.select_all()
        elif event.key() == QtCore.Qt.Key_Z and event.modifiers() & mouse.Event.Ctrl and not event.modifiers() & mouse.Event.Shift:
            self.undo()
        elif event.key() == QtCore.Qt.Key_Z and event.modifiers() & mouse.Event.Ctrl and event.modifiers() & mouse.Event.Shift:
            self.redo()

    def update_scene(self):
        # points
        to_remove = []
        de_points = self.decomposition.points
        for point_id in self.points:
            if point_id not in de_points:
                to_remove.append(point_id)
        for point_id in to_remove:
            self.removeItem(self.points[point_id])
            del self.points[point_id]
        for point_id, point in de_points.items():
            if point_id in self.points:
                self.points[point_id].update()
            else:
                gpt = GsPoint(point)
                self.points[point_id] = gpt
                self.addItem(gpt)

        # segments
        to_remove = []
        de_segments = self.decomposition.segments
        for segment_id in self.segments:
            if segment_id not in de_segments:
                to_remove.append(segment_id)
        for segment_id in to_remove:
            self.removeItem(self.segments[segment_id])
            del self.segments[segment_id]
        for segment_id, segment in de_segments.items():
            if segment_id in self.segments:
                self.segments[segment_id].update()
            else:
                gseg = GsSegment(segment)
                gseg.update_zoom(self._zoom_value)
                self.segments[segment_id] = gseg
                self.addItem(gseg)

        # polygons
        to_remove = []
        de_polygons = self.decomposition.polygons
        for polygon_id in self.polygons:
            if polygon_id not in de_polygons:
                to_remove.append(polygon_id)
        for polygon_id in to_remove:
            self.removeItem(self.polygons[polygon_id])
            del self.polygons[polygon_id]
        for polygon_id, polygon in de_polygons.items():
            if polygon_id == self.outer_id:
                continue
            if polygon_id in self.polygons:
                self.polygons[polygon_id].update()
            else:
                gpol = GsPolygon(polygon)
                self.polygons[polygon_id] = gpol
                self.addItem(gpol)

    def delete_selected(self):
        # segments
        for item in self.selection._selected:
            if type(item) is GsSegment:
                self.decomposition.delete_segment(item.segment)

        # points
        for item in self.selection._selected:
            if type(item) is GsPoint:
                self.decomposition.delete_point(item.pt)

        self.selection._selected.clear()

        self.update_scene()

    def region_panel_changed(self, region_id):
        if self.selection._selected:
            remove = []
            for item in self.selection._selected:
                key = self.get_shape_key(item)
                if not self.regions.set_region(key[0], key[1], region_id):
                    remove.append(item)
            for item in remove:
                self.selection._selected.remove(item)

        self.update_scene()

    @staticmethod
    def get_shape_key(shape):
        if type(shape) is GsPoint:
            return 1, shape.pt.id

        elif type(shape) is GsSegment:
            return 2, shape.segment.id

        elif type(shape) is GsPolygon:
            return 3, shape.polygon_data.id

    def undo(self):
        undo.stack().undo()
        self.update_scene()

    def redo(self):
        undo.stack().redo()
        self.update_scene()


class DiagramView(QtWidgets.QGraphicsView):
    def __init__(self):

        super(DiagramView, self).__init__()
        print(self)


        self._zoom = 0
        self._empty = True
        self._scene = Diagram(self)
        self.setScene(self._scene)

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        #self.setFrameShape(QtWidgets.QFrame.Box)
        #self.ensureVisible(self._scene.sceneRect())
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

        self.el_map = {}



    #def mouseDoubleClickEvent(self, QMouseEvent):
    #    pass


    # def mousePressEvent(self, event):
    #     return super().mousePressEvent(mouse.event_swap_buttons(event, QtCore.QEvent.MouseButtonPress))
    #
    # def mouseReleaseEvent(self, event):
    #     return super().mouseReleaseEvent(mouse.event_swap_buttons(event, QtCore.QEvent.MouseButtonRelease))
    #
    # def mouseMoveEvent(self, event):
    #     return super().mouseMoveEvent(mouse.event_swap_buttons(event, QtCore.QEvent.MouseMove))






    # def hasPhoto(self):
    #     return not self._empty
    #
    # def fitInView(self, scale=True):
    #     rect = QtCore.QRectF(self._photo.pixmap().rect())
    #     if not rect.isNull():
    #         self.setSceneRect(rect)
    #         if self.hasPhoto():
    #             unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
    #             self.scale(1 / unity.width(), 1 / unity.height())
    #             viewrect = self.viewport().rect()
    #             scenerect = self.transform().mapRect(rect)
    #             factor = min(viewrect.width() / scenerect.width(),
    #                          viewrect.height() / scenerect.height())
    #             self.scale(factor, factor)
    #         self._zoom = 0
    #
    # def setPhoto(self, pixmap=None):
    #     self._zoom = 0
    #     if pixmap and not pixmap.isNull():
    #         self._empty = False
    #         self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
    #         self._photo.setPixmap(pixmap)
    #     else:
    #         self._empty = True
    #         self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
    #         self._photo.setPixmap(QtGui.QPixmap())
    #     self.fitInView()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1
        self.scale(factor, factor)

        self._scene.update_zoom(self.transform().m11())

    # def toggleDragMode(self):
    #     if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
    #         self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
    #     elif not self._photo.pixmap().isNull():
    #         self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    # def mousePressEvent(self, event):
    #     if self._photo.isUnderMouse():
    #         self.photoClicked.emit(QtCore.QPoint(event.pos()))
    #     super(PhotoViewer, self).mousePressEvent(event)

    def show_electrodes(self, electrode_groups):
        for eg in electrode_groups:
            reg_id = self._scene.regions.add_region(dim=1)
            for el in eg.electrodes:
                x = el.x
                y = -el.y
                print("x: {}, y: {}".format(x, y))
                pt = self._scene.decomposition.add_point((x, -y))
                self._scene.regions.set_region(1, pt.id, reg_id)
                gpt = GsPoint(pt)
                self._scene.points[pt.id] = gpt
                self._scene.addItem(gpt)
                gpt.update()
                self.el_map[id(el)] = gpt

        self.fitInView(self.scene().itemsBoundingRect(), Qt.KeepAspectRatio)

    def connect_electrodes(self, electrode_group):
        last_gpt = None
        for el in electrode_group.electrodes:
            if id(el) in self.el_map:
                gpt = self.el_map[id(el)]
                if last_gpt is not None:
                    self._scene.add_segment(last_gpt, gpt)
                last_gpt = gpt

    def show_map(self):
        map = QtSvg.QGraphicsSvgItem("bukov_situace.svg")

        # map transform
        # 622380 - 247.266276267186
        # 1128900 - 972.212997362655
        # 1128980 - 1309.97292588439
        map.setTransformOriginPoint(247.266276267186, 972.212997362655)
        map.setScale((1128980 - 1128900) / (1309.97292588439 - 972.212997362655))
        map.setPos(-622380 - 247.266276267186, 1128900 - 972.212997362655)

        self._scene.addItem(map)
        map.setCursor(QtCore.Qt.CrossCursor)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Cursor.setup_cursors()
    mainWindow = DiagramView()
    mainWindow.setGeometry(500, 300, 800, 600)
    mainWindow.show()
    sys.exit(app.exec_())
