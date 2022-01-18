#!/usr/bin/env python
import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets, QtSvg
from PyQt5.QtCore import Qt
from bgem.external import undo
from . import mouse
from bgem.polygons.polygons import PolygonDecomposition, enable_undo
from bgem.gmsh.gmsh_io import GmshIO
from genie.core.data_types import MeshCutToolParam, SideViewToolParam

import random
import os
import math

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
    # _cols = ["cyan", "magenta", "red", "darkRed", "darkCyan", "darkMagenta",
    #          "green", "darkBlue", "yellow","blue"]
    _cols = ["cyan", "magenta", "darkRed", "darkCyan", "darkMagenta",
             "green", "darkBlue", "yellow","blue"]
    # red is used for cut tool
    # _cols = ["darkRed", "darkGreen", "darkBlue", "darkCyan", "darkMagenta", "#808000"]
    # _cols_sel = ["red", "green", "blue", "cyan", "magenta", "yellow"]
    colors = [ QtGui.QColor(col) for col in _cols]
    colors_selected = [QtGui.QColor(col) for col in _cols]
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
        self.setPos(self.pt.xy[0], self.pt.xy[1])
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
        displacement = np.array([x - self.pt.xy[0], y - self.pt.xy[1]])
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



class GsPoint2(QtWidgets.QGraphicsEllipseItem):
    SIZE = 2
    SIZE_SELECTED = 6
    STD_ZVALUE = 21+7
    SELECTED_ZVALUE = 20+7
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

    def __init__(self, x, y, color, color_selected, el_id):
        self.my_x = x
        self.my_y = y
        self.color = color
        self.color_selected = color_selected
        self.selected = False
        self.el_id = el_id
        super().__init__()
        self.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        # do not scale points whenzooming
        #self.setCursor(Cursor.point)
        self.setAcceptedMouseButtons(QtCore.Qt.LeftButton | QtCore.Qt.RightButton)
        self.update()

    def paint(self, painter, option, widget):
        if self.scene().selection.is_selected(self):
            painter.setBrush(GsPoint2.no_brush)
            painter.setPen(self.region_pen)
        else:
            painter.setBrush(self.region_brush)
            painter.setPen(GsPoint2.no_pen)
        painter.drawEllipse(self.rect())

    def update(self):
        self.setPos(self.my_x, self.my_y)

        if self.selected:
            self.region_brush, self.region_pen = GsPoint2.pen_table(self.color_selected)
            self.setRect(-self.SIZE_SELECTED, -self.SIZE_SELECTED, 2 * self.SIZE_SELECTED, 2 * self.SIZE_SELECTED)
            self.setZValue(self.SELECTED_ZVALUE)
        else:
            self.region_brush, self.region_pen = GsPoint2.pen_table(self.color)
            self.setRect(-self.SIZE, -self.SIZE, 2 * self.SIZE, 2 * self.SIZE)
            self.setZValue(self.STD_ZVALUE)

        super().update()

    def set_selected(self, selected=True):
        self.selected = selected
        self.update()


class GsPointCloud(QtWidgets.QGraphicsEllipseItem):
    SIZE = 2
    STD_ZVALUE = -90
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

    def __init__(self, x, y, color):
        self.my_x = x
        self.my_y = y
        self.color = color
        super().__init__()
        self.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        self.setAcceptedMouseButtons(QtCore.Qt.LeftButton | QtCore.Qt.RightButton)
        self.region_brush, self.region_pen = GsPointCloud.pen_table(self.color)
        self.setRect(-self.SIZE, -self.SIZE, 2 * self.SIZE, 2 * self.SIZE)
        self.setBrush(self.region_brush)
        self.setPen(GsPointCloud.no_pen)
        self.update()

    def update(self):
        self.setPos(self.my_x, self.my_y)
        super().update()


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


class MeshCutToolPoint(QtWidgets.QGraphicsRectItem):
    def __init__(self, pen, z, move_fun):
        size = 10
        super().__init__(-size, -size, 2 * size, 2 * size)
        self.setPen(pen)
        self.setZValue(z)
        self.move_fun = move_fun
        self.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCursor(Cursor.point)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            self.move_fun(self.pos())
        return super().itemChange(change, value)


class MeshCutToolPoint2(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, pen, z, move_fun):
        size = 10
        super().__init__(-size, -size, 2 * size, 2 * size)
        self.setPen(pen)
        self.setZValue(z)
        self.move_fun = move_fun
        self.setFlag(QtWidgets.QGraphicsItem.ItemIgnoresTransformations, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCursor(Cursor.point)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            self.move_fun(self.pos())
        return super().itemChange(change, value)


class MeshCutToolLine(QtWidgets.QGraphicsLineItem):
    def __init__(self, pen, z):
        super().__init__()
        self.setPen(pen)
        self.setZValue(z)


class MeshCutTool:
    def __init__(self, scene):
        self._scene = scene

        self.origin = np.array([0.0, 0.0])
        self.gen_vec1 = np.array([40.0, 0.0])
        self.gen_vec2 = np.array([0.0, 20.0])
        self.z_min = 10.0
        self.z_max = 40.0
        self.margin = 5.0
        self.no_inv_factor = 2.0

        pen = QtGui.QPen(QtGui.QColor("red"), 1.5, QtCore.Qt.SolidLine)
        pen.setCosmetic(True)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        margin_pen = QtGui.QPen(QtGui.QColor("red"), 0.5, QtCore.Qt.SolidLine)
        margin_pen.setCosmetic(True)
        z = 30

        # create items
        self.point0 = MeshCutToolPoint(pen, z, self.point0_move_to)
        self.point1 = MeshCutToolPoint2(pen, z, self.point1_move_to)
        self.point2 = MeshCutToolPoint2(pen, z, self.point2_move_to)
        self.point3 = MeshCutToolPoint2(pen, z, self.point3_move_to)
        self.line1 = MeshCutToolLine(pen, z)
        self.line2 = MeshCutToolLine(pen, z)
        self.line3 = MeshCutToolLine(pen, z)
        self.line4 = MeshCutToolLine(pen, z)
        self.margin_line1 = MeshCutToolLine(margin_pen, z)
        self.margin_line2 = MeshCutToolLine(margin_pen, z)
        self.margin_line3 = MeshCutToolLine(margin_pen, z)
        self.margin_line4 = MeshCutToolLine(margin_pen, z)

        # add items to scene
        self._scene.addItem(self.line1)
        self._scene.addItem(self.line2)
        self._scene.addItem(self.line3)
        self._scene.addItem(self.line4)
        self._scene.addItem(self.point3)
        self._scene.addItem(self.point0)
        self._scene.addItem(self.point1)
        self._scene.addItem(self.point2)
        self._scene.addItem(self.margin_line1)
        self._scene.addItem(self.margin_line2)
        self._scene.addItem(self.margin_line3)
        self._scene.addItem(self.margin_line4)

        self.update()

    def update(self):
        # corner points
        a = self.origin
        b = a + self.gen_vec1
        c = b + self.gen_vec2
        d = a + self.gen_vec2

        # margin corner points
        # m = self.margin
        # l1 = np.linalg.norm(self.gen_vec1)
        # l2 = np.linalg.norm(self.gen_vec2)
        # if l1 < 1e-12:
        #     g1n = self.gen_vec1
        # else:
        #     g1n = self.gen_vec1 / l1
        # if l2 < 1e-12:
        #     g2n = self.gen_vec2
        # else:
        #     g2n = self.gen_vec2 / l2
        # am = a - g1n * m - g2n * m
        # bm = b + g1n * m - g2n * m
        # cm = c + g1n * m + g2n * m
        # dm = d - g1n * m + g2n * m

        # no inv corner points
        g1 = self.gen_vec1
        g2 = self.gen_vec2
        k = (self.no_inv_factor - 1) * 0.5
        am = a - g1 * k - g2 * k
        bm = b + g1 * k - g2 * k
        cm = c + g1 * k + g2 * k
        dm = d - g1 * k + g2 * k

        # set new positions
        self.line1.setLine(a[0], a[1], b[0], b[1])
        self.line2.setLine(b[0], b[1], c[0], c[1])
        self.line3.setLine(c[0], c[1], d[0], d[1])
        self.line4.setLine(d[0], d[1], a[0], a[1])
        self.point0.setPos(a[0], a[1])
        self.point1.setPos(b[0], b[1])
        self.point2.setPos(d[0], d[1])
        self.point3.setPos(c[0], c[1])
        self.margin_line1.setLine(am[0], am[1], bm[0], bm[1])
        self.margin_line2.setLine(bm[0], bm[1], cm[0], cm[1])
        self.margin_line3.setLine(cm[0], cm[1], dm[0], dm[1])
        self.margin_line4.setLine(dm[0], dm[1], am[0], am[1])

    def point0_move_to(self, pos):
        self.origin = np.array([pos.x(), pos.y()])
        self.update()
        #self.print_pos()
        self._scene.mesh_cut_tool_changed.emit()

    def point1_move_to(self, pos):
        self.gen_vec1 = np.array([pos.x(), pos.y()]) - self.origin
        self.update()
        #self.print_pos()
        self._scene.mesh_cut_tool_changed.emit()

    def point2_move_to(self, pos):
        self.gen_vec2 = np.array([pos.x(), pos.y()]) - self.origin
        self.update()
        #self.print_pos()
        self._scene.mesh_cut_tool_changed.emit()

    def point3_move_to(self, pos):
        if np.abs(np.linalg.det(np.array([self.gen_vec1, self.gen_vec2]))) > 1e-12:
            g1n = self.gen_vec1 / np.linalg.norm(self.gen_vec1)
            g2n = self.gen_vec2 / np.linalg.norm(self.gen_vec2)
            ac = np.array([pos.x(), pos.y()]) - self.origin

            tr = np.array([g1n, g2n]).T
            inv_tr = np.linalg.inv(tr)
            ac_tr = inv_tr @ ac

            self.gen_vec1 = g1n * ac_tr[0]
            self.gen_vec2 = g2n * ac_tr[1]
        self.update()
        #self.print_pos()
        self._scene.mesh_cut_tool_changed.emit()

    def print_pos(self):
        print("base_point = np.array([{}, {}, {}])".format(self.origin[0] + 622000, -self.origin[1] + 1128000, self.z_min))
        print("gen_vecs = [np.array([{}, {}, {}]), np.array([{}, {}, {}]), np.array([{}, {}, {}])]"
              .format(self.gen_vec1[0], -self.gen_vec1[1], 0,
                      self.gen_vec2[0], -self.gen_vec2[1], 0,
                      0, 0, self.z_max - self.z_min))

    def from_mesh_cut_tool_param(self, param):
        self.origin = np.array([param.origin_x, param.origin_y])
        self.gen_vec1 = np.array([param.gen_vec1_x, param.gen_vec1_y])
        self.gen_vec2 = np.array([param.gen_vec2_x, param.gen_vec2_y])
        self.z_min = param.z_min
        self.z_max = param.z_max
        self.margin = param.margin
        self.no_inv_factor = param.no_inv_factor

        self.update()

    def to_mesh_cut_tool_param(self):
        cut_tool = MeshCutToolParam()
        cut_tool.origin_x = self.origin[0]
        cut_tool.origin_y = self.origin[1]
        cut_tool.gen_vec1_x = self.gen_vec1[0]
        cut_tool.gen_vec1_y = self.gen_vec1[1]
        cut_tool.gen_vec2_x = self.gen_vec2[0]
        cut_tool.gen_vec2_y = self.gen_vec2[1]
        cut_tool.z_min = self.z_min
        cut_tool.z_max = self.z_max
        cut_tool.no_inv_factor = self.no_inv_factor
        return cut_tool


class SideViewTool:
    def __init__(self, scene):
        self._scene = scene

        self.origin = np.array([0.0, 0.0])
        self.dir_vec = np.array([0.0, 20.0])

        pen = QtGui.QPen(QtGui.QColor("blue"), 1.5, QtCore.Qt.SolidLine)
        pen.setCosmetic(True)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        margin_pen = QtGui.QPen(QtGui.QColor("blue"), 0.5, QtCore.Qt.SolidLine)
        margin_pen.setCosmetic(True)
        z = 31

        # create items
        self.point0 = MeshCutToolPoint(pen, z, self.point0_move_to)
        self.point1 = MeshCutToolPoint2(pen, z, self.point1_move_to)
        self.line1 = MeshCutToolLine(pen, z)
        self.margin_line1 = MeshCutToolLine(margin_pen, z)

        # add items to scene
        self._scene.addItem(self.line1)
        self._scene.addItem(self.point0)
        self._scene.addItem(self.point1)
        self._scene.addItem(self.margin_line1)

        self.update()

    def update(self):
        # corner points
        a = self.origin
        b = a + self.dir_vec

        l = np.linalg.norm(self.dir_vec)
        if l < 1e-12:
            n = np.array([0.0, 1.0])
        else:
            n = self.dir_vec / l
        am = a + np.array([n[1], -n[0]]) * 1e3
        bm = a + np.array([-n[1], n[0]]) * 1e3

        # set new positions
        self.line1.setLine(a[0], a[1], b[0], b[1])
        self.point0.setPos(a[0], a[1])
        self.point1.setPos(b[0], b[1])
        self.margin_line1.setLine(am[0], am[1], bm[0], bm[1])

    def point0_move_to(self, pos):
        self.origin = np.array([pos.x(), pos.y()])
        self.update()
        self._scene.side_view_tool_changed.emit()

    def point1_move_to(self, pos):
        self.dir_vec = np.array([pos.x(), pos.y()]) - self.origin
        self.update()
        self._scene.side_view_tool_changed.emit()

    def from_side_view_tool_param(self, param):
        self.origin = np.array([param.origin_x, param.origin_y])
        self.dir_vec = np.array([param.dir_vec_x, param.dir_vec_y])

        self.update()

    def to_side_view_tool_param(self):
        cut_tool = SideViewToolParam()
        cut_tool.origin_x = self.origin[0]
        cut_tool.origin_y = self.origin[1]
        cut_tool.dir_vec_x = self.dir_vec[0]
        cut_tool.dir_vec_y = self.dir_vec[1]
        return cut_tool

    def transform(self, x, y, z, nd):
        xt = self.origin[0] + (x - self.origin[0]) * nd[1] - (y - self.origin[1]) * nd[0]
        yt = z
        zt = (y - self.origin[1]) * nd[1] + (x - self.origin[0]) * nd[0]

        return xt, yt, zt


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
    mesh_cut_tool_changed = QtCore.pyqtSignal()
    # cut tool changed
    side_view_tool_changed = QtCore.pyqtSignal()
    # side view tool changed

    def __init__(self, parent):
        super().__init__(parent)
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

        self.mesh_cut_tool = MeshCutTool(self)
        self.side_view_tool = SideViewTool(self)

        self.electrode_item_list = []
        self.pixmap_item = None
        self.point_cloud_item_list = []
        self.map_item = None
        self.gallery_mesh_lines = []

        self.my_scene_rect = QtCore.QRect()

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

        # if event.button() == mouse.Event.Left and screen_pos_not_changed:
        #     self.mouse_create_event(event)

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

    def updata_screen_rect(self):
        rect = QtCore.QRectF()

        for e in self.electrode_item_list:
            rect = rect.united(e.sceneBoundingRect())

        # if self.pixmap_item:
        #     rect = rect.united(self.pixmap_item.sceneBoundingRect())

        for p in self.point_cloud_item_list:
            rect = rect.united(p.sceneBoundingRect())

        if self.map_item:
            rect = rect.united(self.map_item.sceneBoundingRect())

        for line in self.gallery_mesh_lines:
            rect = rect.united(line.sceneBoundingRect())

        if rect.isEmpty():
            rect = QtCore.QRectF(-100, -100, 200, 200)

        self.my_scene_rect = rect

        w = rect.width()
        h = rect.height()
        rect = rect.marginsAdded(QtCore.QMarginsF(w, h, w, h))

        self.setSceneRect(rect)

    def mySceneRect(self):
        return self.my_scene_rect


class DiagramView(QtWidgets.QGraphicsView):
    def __init__(self, side_view):
        super(DiagramView, self).__init__()

        self.side_view = side_view
        self.side_view.diagram_view = self

        self._zoom = 0
        self.scale(1, -1)
        #self._empty = True
        self._scene = Diagram(self)
        self.setScene(self._scene)

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        #self.setFrameShape(QtWidgets.QFrame.Box)
        #self.ensureVisible(self._scene.sceneRect())
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

        self.el_map = {}

        self.no_scroll = False
        self.y_center = 0.0



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
        self.side_view.no_scroll = True

        if event.angleDelta().y() > 0:
            factor = 1.25
            self._zoom += 1
        else:
            factor = 0.8
            self._zoom -= 1
        self.scale(factor, factor)

        self._scene.update_zoom(self.transform().m11())

        self.side_view.save_y_center()
        self.side_view.setTransform(self.transform())

        self.side_view.no_scroll = False

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        if not self.no_scroll:
            no_scroll = self.side_view.no_scroll
            self.side_view.no_scroll = True
            dcx = self.mapToScene(self.viewport().geometry().center()).x()
            self.side_view.centerOn(dcx, self.side_view.y_center)
            self.side_view.no_scroll = no_scroll

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.side_view.save_y_center()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.save_y_center()

    def save_y_center(self):
        self.y_center = self.mapToScene(self.viewport().geometry().center()).y()

    # def toggleDragMode(self):
    #     if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
    #         self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
    #     elif not self._photo.pixmap().isNull():
    #         self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    # def mousePressEvent(self, event):
    #     if self._photo.isUnderMouse():
    #         self.photoClicked.emit(QtCore.QPoint(event.pos()))
    #     super(PhotoViewer, self).mousePressEvent(event)

    def show_electrodes_old(self, electrode_groups):
        for eg in electrode_groups:
            reg_id = self._scene.regions.add_region(dim=1)
            for el in eg.electrodes:
                x = el.x
                y = -el.y
                #print("x: {}, y: {}".format(x, y))
                pt = self._scene.decomposition.add_point((x, -y))
                self._scene.regions.set_region(1, pt.id, reg_id)
                gpt = GsPoint(pt)
                self._scene.points[pt.id] = gpt
                self._scene.addItem(gpt)
                gpt.update()
                self.el_map[id(el)] = gpt

        self.fitInView(self.scene().itemsBoundingRect(), Qt.KeepAspectRatio)

    def show_electrodes(self, electrode_groups):
        self.hide_electrodes()

        color_ind = 0
        for eg in electrode_groups:
            for el in eg.electrodes:
                x = el.x
                y = el.y
                gpt = GsPoint2(x, y, Region.colors[color_ind % len(Region.colors)].name(),
                               Region.colors_selected[color_ind % len(Region.colors)].name(),
                               el.id)
                self._scene.addItem(gpt)
                gpt.update()
                self.el_map[id(el)] = gpt
                self._scene.electrode_item_list.append(gpt)
            color_ind += 1

        self.side_view.show_electrodes(electrode_groups)

    def hide_electrodes(self):
        for item in self.el_map.values():
            self._scene.removeItem(item)
        self.el_map.clear()
        self._scene.electrode_item_list.clear()

        self.side_view.hide_electrodes()

    def update_selected_electrodes(self, selected_el):
        el = set(selected_el)
        for item in self._scene.electrode_item_list:
            item.set_selected(item.el_id in el)

        self.side_view.update_selected_electrodes(selected_el)

    def show_laser(self, file_name):
        reg_id = self._scene.regions.add_region(dim=1)
        with open(file_name) as fd:
            for i, line in enumerate(fd):
                #if i % 1000 != 0:
                if random.random() > 0.001:
                    continue
                #print(line)
                s = line.split()
                if len(s) >= 3:
                    x = float(s[0]) - 622000
                    y = -float(s[1]) + 1128000
                    print("x: {}, y: {}".format(x, y))
                    pt = self._scene.decomposition.add_point((x, -y))
                    self._scene.regions.set_region(1, pt.id, reg_id)
                    gpt = GsPoint(pt)
                    self._scene.points[pt.id] = gpt
                    self._scene.addItem(gpt)
                    gpt.update()

        self.fitInView(self.scene().itemsBoundingRect(), Qt.KeepAspectRatio)

    def show_laser2(self, file_name):
        def xy_gen(fd):
            line = fd.readline()
            while line:
                s = line.split()
                if len(s) >= 3:
                    x = float(s[0]) - 622000
                    y = -float(s[1]) + 1128000
                    yield x, y
                line = fd.readline()

        with open(file_name) as fd:
            # determine range
            gen = xy_gen(fd)
            x, y = next(gen)
            x_min = x_max = x
            y_min = y_max = y
            for x, y in gen:
                if x < x_min:
                    x_min = x
                elif x > x_max:
                    x_max = x
                if y < y_min:
                    y_min = y
                elif y > y_max:
                    y_max = y

            # create pixmap
            fd.seek(0)
            x_max_min = x_max - x_min
            y_max_min = y_max - y_min
            max_min = max(x_max_min, y_max_min)
            pixmap_size = 1000
            max_min_pixmap_size = max_min / pixmap_size
            pixmap = QtGui.QPixmap(x_max_min / max_min_pixmap_size, y_max_min / max_min_pixmap_size)
            pixmap.fill(Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            pen = QtGui.QPen(QtGui.QColor("green"))
            painter.setPen(pen)
            for x, y in xy_gen(fd):
                painter.drawPoint((x - x_min) / max_min_pixmap_size, (y - y_min) / max_min_pixmap_size)
            painter.end()

            # pixmap item
            pixmap_item = QtWidgets.QGraphicsPixmapItem(pixmap)
            pixmap_item.setZValue(25)
            pixmap_item.setTransformOriginPoint(x_min, y_min)
            pixmap_item.setScale(max_min_pixmap_size)
            pixmap_item.setOffset(x_min, y_min)
            self._scene.addItem(pixmap_item)

        self.fitInView(self.scene().itemsBoundingRect(), Qt.KeepAspectRatio)

    def show_laser_mesh(self, file_name):
        pen = QtGui.QPen(QtGui.QColor("green"), 0, QtCore.Qt.SolidLine)

        def add_line(a, b):
            line = QtWidgets.QGraphicsLineItem()
            line.setZValue(1)
            line.setPen(pen)
            line.setLine(a[0] - 622000, -a[1] + 1128000, b[0] - 622000, -b[1] + 1128000)
            self._scene.addItem(line)

        mesh = GmshIO(file_name)
        for data in mesh.elements.values():
            type_, tags, nodeIDs = data
            a = mesh.nodes[nodeIDs[0]]
            b = mesh.nodes[nodeIDs[1]]
            c = mesh.nodes[nodeIDs[2]]

            add_line(a, b)
            add_line(b, c)
            add_line(c, a)

        self.fitInView(self.scene().itemsBoundingRect(), Qt.KeepAspectRatio)

    def connect_electrodes(self, electrode_group):
        last_gpt = None
        for el in electrode_group.electrodes:
            if id(el) in self.el_map:
                gpt = self.el_map[id(el)]
                if last_gpt is not None:
                    self._scene.add_segment(last_gpt, gpt)
                last_gpt = gpt

    def show_map(self, genie):
        self.hide_map()

        prj_dir = genie.cfg.current_project_dir
        cfg = genie.project_cfg

        if not cfg.map_file_name:
            return
        map_file = os.path.join(prj_dir, cfg.map_file_name)
        if map_file.lower().endswith(".svg"):
            map_item = QtSvg.QGraphicsSvgItem(map_file)
        else:
            pixmap = QtGui.QPixmap(map_file)
            map_item = QtWidgets.QGraphicsPixmapItem(pixmap)

        mtr = cfg.map_transform
        tr = QtGui.QTransform(mtr.m11, mtr.m12, mtr.m21, mtr.m22, mtr.dx, mtr.dy)
        map_item.setTransform(tr)

        map_item.setZValue(-100)

        self._scene.addItem(map_item)
        map_item.setCursor(QtCore.Qt.CrossCursor)

        self._scene.map_item = map_item

    def hide_map(self):
        if self._scene.map_item is not None:
            self._scene.removeItem(self._scene.map_item)
            self._scene.map_item = None

    def show_map_old(self):
        file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "res", "bukov_situace.svg")
        map = QtSvg.QGraphicsSvgItem(file)

        # map transform
        # 622380 - 247.266276267186
        # 1128900 - 972.212997362655
        # 1128980 - 1309.97292588439
        map.setTransformOriginPoint(247.266276267186, 972.212997362655)
        map.setScale((1128980 - 1128900) / (1309.97292588439 - 972.212997362655))
        map.setPos(-622380 - 247.266276267186, 1128900 - 972.212997362655)

        self._scene.addItem(map)
        map.setCursor(QtCore.Qt.CrossCursor)

    def show_pixmap(self, genie):
        self.hide_pixmap()

        prj_dir = genie.cfg.current_project_dir
        cfg = genie.project_cfg
        file = os.path.join(prj_dir, "point_cloud_pixmap.png")
        if not os.path.isfile(file):
            return
        pixmap = QtGui.QPixmap(file)
        pixmap_item = QtWidgets.QGraphicsPixmapItem(pixmap.transformed(QtGui.QTransform.fromScale(1, -1)))

        pixmap_item.setZValue(-90)
        pixmap_item.setOpacity(0.5)
        offset_x = cfg.point_cloud_origin_x + cfg.point_cloud_pixmap_x_min
        offset_y = cfg.point_cloud_origin_y + cfg.point_cloud_pixmap_y_min
        pixmap_item.setTransformOriginPoint(offset_x, offset_y)
        pixmap_item.setScale(cfg.point_cloud_pixmap_scale)
        pixmap_item.setOffset(offset_x, offset_y)
        self._scene.addItem(pixmap_item)

        self._scene.pixmap_item = pixmap_item

    def hide_pixmap(self):
        if self._scene.pixmap_item is not None:
            self._scene.removeItem(self._scene.pixmap_item)
            self._scene.pixmap_item = None

    def show_point_cloud(self, genie):
        self.hide_point_cloud()

        prj_dir = genie.cfg.current_project_dir
        cfg = genie.project_cfg
        file = os.path.join(prj_dir, "point_cloud_red.xyz")
        if not os.path.isfile(file):
            return

        with open(file) as fd:
            for line in fd:
                s = line.split()
                if len(s) < 3:
                    continue

                x = float(s[0]) + cfg.point_cloud_origin_x
                y = float(s[1]) + cfg.point_cloud_origin_y

                gpt = GsPointCloud(x, y, "black")
                self._scene.addItem(gpt)
                gpt.setZValue(-90)
                gpt.setOpacity(0.5)
                gpt.update()
                self._scene.point_cloud_item_list.append(gpt)

        self.side_view.show_point_cloud(genie)

    def hide_point_cloud(self):
        for item in self._scene.point_cloud_item_list:
            self._scene.removeItem(item)
        self._scene.point_cloud_item_list.clear()

        self.side_view.hide_point_cloud()

    def show_gallery_mesh(self, genie):
        self.hide_gallery_mesh()

        prj_dir = genie.cfg.current_project_dir
        cfg = genie.project_cfg
        file_name = os.path.join(prj_dir, "gallery_mesh.msh")
        if not os.path.isfile(file_name):
            return

        pen = QtGui.QPen(QtGui.QColor("black"), 0, QtCore.Qt.SolidLine)

        mesh = GmshIO(file_name)

        lines = set()

        def add_line(n1, n2):
            if (n1, n2) in lines or (n1, n2) in lines:
                return
            else:
                lines.add((n1, n2))

            a = mesh.nodes[n1]
            b = mesh.nodes[n2]

            line = QtWidgets.QGraphicsLineItem(a[0] + cfg.gallery_mesh_origin_x, a[1] + cfg.gallery_mesh_origin_y,
                                               b[0] + cfg.gallery_mesh_origin_x, b[1] + cfg.gallery_mesh_origin_y)
            line.setZValue(-80)
            line.setPen(pen)
            self._scene.addItem(line)
            self._scene.gallery_mesh_lines.append(line)

        for data in mesh.elements.values():
            type_, tags, nodeIDs = data
            if type_ != 2:
                continue
            a = nodeIDs[0]
            b = nodeIDs[1]
            c = nodeIDs[2]

            add_line(a, b)
            add_line(b, c)
            add_line(c, a)

        self.side_view.show_gallery_mesh(genie)

    def hide_gallery_mesh(self):
        for item in self._scene.gallery_mesh_lines:
            self._scene.removeItem(item)
        self._scene.gallery_mesh_lines.clear()

        self.side_view.hide_gallery_mesh()


class SideMeshCutTool:
    def __init__(self, scene):
        self._scene = scene

        pen = QtGui.QPen(QtGui.QColor("red"), 1.5, QtCore.Qt.SolidLine)
        pen.setCosmetic(True)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        margin_pen = QtGui.QPen(QtGui.QColor("red"), 0.5, QtCore.Qt.SolidLine)
        margin_pen.setCosmetic(True)
        z = 30

        # create items
        self.point0 = MeshCutToolPoint(pen, z, self.point0_move_to)
        self.point1 = MeshCutToolPoint(pen, z, self.point1_move_to)
        self.line1 = MeshCutToolLine(pen, z)
        self.line2 = MeshCutToolLine(pen, z)
        self.line3 = MeshCutToolLine(pen, z)
        self.line4 = MeshCutToolLine(pen, z)
        self.line1_b = MeshCutToolLine(pen, z)
        self.line2_b = MeshCutToolLine(pen, z)
        self.line3_b = MeshCutToolLine(pen, z)
        self.line4_b = MeshCutToolLine(pen, z)
        self.line_a = MeshCutToolLine(pen, z)
        self.line_b = MeshCutToolLine(pen, z)
        self.line_c = MeshCutToolLine(pen, z)
        self.line_d = MeshCutToolLine(pen, z)
        self.margin_line1 = MeshCutToolLine(margin_pen, z)
        self.margin_line2 = MeshCutToolLine(margin_pen, z)
        self.margin_line3 = MeshCutToolLine(margin_pen, z)
        self.margin_line4 = MeshCutToolLine(margin_pen, z)
        self.margin_line1_b = MeshCutToolLine(margin_pen, z)
        self.margin_line2_b = MeshCutToolLine(margin_pen, z)
        self.margin_line3_b = MeshCutToolLine(margin_pen, z)
        self.margin_line4_b = MeshCutToolLine(margin_pen, z)
        self.margin_line_a = MeshCutToolLine(margin_pen, z)
        self.margin_line_b = MeshCutToolLine(margin_pen, z)
        self.margin_line_c = MeshCutToolLine(margin_pen, z)
        self.margin_line_d = MeshCutToolLine(margin_pen, z)

        # add items to scene
        self._scene.addItem(self.line1)
        self._scene.addItem(self.line2)
        self._scene.addItem(self.line3)
        self._scene.addItem(self.line4)
        self._scene.addItem(self.line1_b)
        self._scene.addItem(self.line2_b)
        self._scene.addItem(self.line3_b)
        self._scene.addItem(self.line4_b)
        self._scene.addItem(self.line_a)
        self._scene.addItem(self.line_b)
        self._scene.addItem(self.line_c)
        self._scene.addItem(self.line_d)
        self._scene.addItem(self.point0)
        self._scene.addItem(self.point1)
        self._scene.addItem(self.margin_line1)
        self._scene.addItem(self.margin_line2)
        self._scene.addItem(self.margin_line3)
        self._scene.addItem(self.margin_line4)
        self._scene.addItem(self.margin_line1_b)
        self._scene.addItem(self.margin_line2_b)
        self._scene.addItem(self.margin_line3_b)
        self._scene.addItem(self.margin_line4_b)
        self._scene.addItem(self.margin_line_a)
        self._scene.addItem(self.margin_line_b)
        self._scene.addItem(self.margin_line_c)
        self._scene.addItem(self.margin_line_d)

        self.update()

    def update(self):
        if self._scene.diagram is None:
            return
        mct = self._scene.diagram.mesh_cut_tool
        svt = self._scene.diagram.side_view_tool
        nd = svt.dir_vec / np.linalg.norm(svt.dir_vec)

        # corner points
        a = mct.origin
        b = a + mct.gen_vec1
        c = b + mct.gen_vec2
        d = a + mct.gen_vec2

        ax, _, _ = svt.transform(a[0], a[1], 0, nd)
        bx, _, _ = svt.transform(b[0], b[1], 0, nd)
        cx, _, _ = svt.transform(c[0], c[1], 0, nd)
        dx, _, _ = svt.transform(d[0], d[1], 0, nd)

        # no inv corner points
        g1 = mct.gen_vec1
        g2 = mct.gen_vec2
        gv3 = mct.z_max - mct.z_min
        k = (mct.no_inv_factor - 1) * 0.5
        am = a - g1 * k - g2 * k
        bm = b + g1 * k - g2 * k
        cm = c + g1 * k + g2 * k
        dm = d - g1 * k + g2 * k
        z_min_m = mct.z_min - gv3 * k
        z_max_m = mct.z_max + gv3 * k

        amx, _, _ = svt.transform(am[0], am[1], 0, nd)
        bmx, _, _ = svt.transform(bm[0], bm[1], 0, nd)
        cmx, _, _ = svt.transform(cm[0], cm[1], 0, nd)
        dmx, _, _ = svt.transform(dm[0], dm[1], 0, nd)

        # z points
        z = (a + c) / 2
        z_x, _, _ = svt.transform(z[0], z[1], 0, nd)

        # set new positions
        self.line1.setLine(ax, mct.z_max, bx, mct.z_max)
        self.line2.setLine(bx, mct.z_max, cx, mct.z_max)
        self.line3.setLine(cx, mct.z_max, dx, mct.z_max)
        self.line4.setLine(dx, mct.z_max, ax, mct.z_max)
        self.line1_b.setLine(ax, mct.z_min, bx, mct.z_min)
        self.line2_b.setLine(bx, mct.z_min, cx, mct.z_min)
        self.line3_b.setLine(cx, mct.z_min, dx, mct.z_min)
        self.line4_b.setLine(dx, mct.z_min, ax, mct.z_min)
        self.line_a.setLine(ax, mct.z_min, ax, mct.z_max)
        self.line_b.setLine(bx, mct.z_min, bx, mct.z_max)
        self.line_c.setLine(cx, mct.z_min, cx, mct.z_max)
        self.line_d.setLine(dx, mct.z_min, dx, mct.z_max)
        self.point0.setPos(z_x, mct.z_max)
        self.point1.setPos(z_x, mct.z_min)
        self.margin_line1.setLine(amx, z_max_m, bmx, z_max_m)
        self.margin_line2.setLine(bmx, z_max_m, cmx, z_max_m)
        self.margin_line3.setLine(cmx, z_max_m, dmx, z_max_m)
        self.margin_line4.setLine(dmx, z_max_m, amx, z_max_m)
        self.margin_line1_b.setLine(amx, z_min_m, bmx, z_min_m)
        self.margin_line2_b.setLine(bmx, z_min_m, cmx, z_min_m)
        self.margin_line3_b.setLine(cmx, z_min_m, dmx, z_min_m)
        self.margin_line4_b.setLine(dmx, z_min_m, amx, z_min_m)
        self.margin_line_a.setLine(amx, z_min_m, amx, z_max_m)
        self.margin_line_b.setLine(bmx, z_min_m, bmx, z_max_m)
        self.margin_line_c.setLine(cmx, z_min_m, cmx, z_max_m)
        self.margin_line_d.setLine(dmx, z_min_m, dmx, z_max_m)

    def point0_move_to(self, pos):
        if self._scene.diagram is None:
            return
        mct = self._scene.diagram.mesh_cut_tool
        mct.z_max = pos.y()
        self.update()
        self._scene.diagram.mesh_cut_tool_changed.emit()

    def point1_move_to(self, pos):
        if self._scene.diagram is None:
            return
        mct = self._scene.diagram.mesh_cut_tool
        mct.z_min = pos.y()
        self.update()
        self._scene.diagram.mesh_cut_tool_changed.emit()


class SideScene(QtWidgets.QGraphicsScene):
    def __init__(self, parent):
        super().__init__(parent)

        self.diagram = None

        self.side_mesh_cut_tool = SideMeshCutTool(self)

        self.selection = Selection(self)

        self.electrode_item_list = []
        self.electrode_pos_list = []
        self.point_cloud_item_list = []
        self.point_cloud_pos_list = []
        self.pixmap_item = None
        self.map_item = None
        self.gallery_mesh_lines = []
        self.gallery_mesh_pos_list = []

    def updata_screen_rect(self):
        rect = QtCore.QRectF()

        for e in self.electrode_item_list:
            rect = rect.united(e.sceneBoundingRect())

        for p in self.point_cloud_item_list:
            rect = rect.united(p.sceneBoundingRect())

        if self.diagram.map_item:
            svt = self.diagram.side_view_tool
            nd = svt.dir_vec / np.linalg.norm(svt.dir_vec)
            r = self.diagram.map_item.sceneBoundingRect()

            def tr(p):
                x, _, _ = svt.transform(p.x(), p.y(), 0, nd)
                return QtCore.QRectF(x, rect.top(), 0, 0)

            rect = rect.united(tr(r.topLeft()))
            rect = rect.united(tr(r.topRight()))
            rect = rect.united(tr(r.bottomLeft()))
            rect = rect.united(tr(r.bottomRight()))

        for line in self.gallery_mesh_lines:
            rect = rect.united(line.sceneBoundingRect())

        if rect.isEmpty():
            rect = QtCore.QRectF(-100, -100, 200, 200)

        w = rect.width()
        h = rect.height()
        rect = rect.marginsAdded(QtCore.QMarginsF(w, h, w, h))

        self.setSceneRect(rect)


class SideView(QtWidgets.QGraphicsView):
    def __init__(self):
        super().__init__()

        self.diagram_view = None

        self._scene = SideScene(self)
        self.setScene(self._scene)

        self.scale(1, -1)

        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

        self.el_map = {}

        self.no_scroll = False
        self.y_center = 0.0

    def show_electrodes(self, electrode_groups):
        svt = self.diagram_view._scene.side_view_tool
        nd = svt.dir_vec / np.linalg.norm(svt.dir_vec)

        self.hide_electrodes()

        color_ind = 0
        for eg in electrode_groups:
            for el in eg.electrodes:
                x, y, _ = svt.transform(el.x, el.y, el.z, nd)
                gpt = GsPoint2(x, y, Region.colors[color_ind % len(Region.colors)].name(),
                               Region.colors_selected[color_ind % len(Region.colors)].name(),
                               el.id)
                self._scene.addItem(gpt)
                gpt.update()
                self.el_map[id(el)] = gpt
                self._scene.electrode_item_list.append(gpt)
                self._scene.electrode_pos_list.append((el.x, el.y, el.z))
            color_ind += 1

    def hide_electrodes(self):
        for item in self.el_map.values():
            self._scene.removeItem(item)
        self.el_map.clear()
        self._scene.electrode_item_list.clear()
        self._scene.electrode_pos_list.clear()

    def update_selected_electrodes(self, selected_el):
        el = set(selected_el)
        for item in self._scene.electrode_item_list:
            item.set_selected(item.el_id in el)

    def update_electrodes_pos(self):
        svt = self.diagram_view._scene.side_view_tool
        nd = svt.dir_vec / np.linalg.norm(svt.dir_vec)

        for i in range(len(self._scene.electrode_item_list)):
            gpt = self._scene.electrode_item_list[i]
            pos = self._scene.electrode_pos_list[i]
            gpt.my_x, gpt.my_y, z = svt.transform(pos[0], pos[1], pos[2], nd)
            gpt.setVisible(z >= 0)
            gpt.update()

    def show_point_cloud(self, genie):
        svt = self.diagram_view._scene.side_view_tool
        nd = svt.dir_vec / np.linalg.norm(svt.dir_vec)

        self.hide_point_cloud()

        prj_dir = genie.cfg.current_project_dir
        cfg = genie.project_cfg
        file = os.path.join(prj_dir, "point_cloud_red.xyz")
        if not os.path.isfile(file):
            return

        with open(file) as fd:
            for line in fd:
                s = line.split()
                if len(s) < 3:
                    continue

                x = float(s[0]) + cfg.point_cloud_origin_x
                y = float(s[1]) + cfg.point_cloud_origin_y
                z = float(s[2]) + cfg.point_cloud_origin_z

                xt, yt, zt = svt.transform(x, y, z, nd)

                gpt = GsPointCloud(xt, yt, "black")
                self._scene.addItem(gpt)
                gpt.setZValue(-90)
                gpt.setOpacity(0.5)
                gpt.update()
                self._scene.point_cloud_item_list.append(gpt)
                self._scene.point_cloud_pos_list.append((x, y, z))

    def hide_point_cloud(self):
        for item in self._scene.point_cloud_item_list:
            self._scene.removeItem(item)
        self._scene.point_cloud_item_list.clear()
        self._scene.point_cloud_pos_list.clear()

    def update_point_cloud_pos(self):
        svt = self.diagram_view._scene.side_view_tool
        dir_vec_len = np.linalg.norm(svt.dir_vec)
        nd = svt.dir_vec / dir_vec_len

        for i in range(len(self._scene.point_cloud_item_list)):
            gpt = self._scene.point_cloud_item_list[i]
            pos = self._scene.point_cloud_pos_list[i]
            gpt.my_x, gpt.my_y, z = svt.transform(pos[0], pos[1], pos[2], nd)
            #gpt.setVisible(z >= 0)

            # linear
            # if z >= 0:
            #     if z > 100:
            #         op = 0.25
            #     else:
            #         op = 0.75 - z / 200
            #     gpt.setOpacity(op)

            # only 2 values
            #if z >= 0:
            if -dir_vec_len < z < dir_vec_len:
                op = 0.75
            else:
                op = 0.05
            gpt.setOpacity(op)

            # logaritmic
            # if z >= 0:
            #     op = 1 - math.log(z) / 10
            #     gpt.setOpacity(op)

            gpt.update()

    def show_gallery_mesh(self, genie):
        svt = self.diagram_view._scene.side_view_tool
        nd = svt.dir_vec / np.linalg.norm(svt.dir_vec)

        self.hide_gallery_mesh()

        prj_dir = genie.cfg.current_project_dir
        cfg = genie.project_cfg
        file_name = os.path.join(prj_dir, "gallery_mesh.msh")
        if not os.path.isfile(file_name):
            return

        pen = QtGui.QPen(QtGui.QColor("black"), 0, QtCore.Qt.SolidLine)

        mesh = GmshIO(file_name)

        lines = set()

        def add_line(n1, n2):
            if (n1, n2) in lines or (n1, n2) in lines:
                return
            else:
                lines.add((n1, n2))

            a = mesh.nodes[n1]
            b = mesh.nodes[n2]

            x1 = a[0] + cfg.gallery_mesh_origin_x
            y1 = a[1] + cfg.gallery_mesh_origin_y
            z1 = a[2] + cfg.gallery_mesh_origin_z
            x2 = b[0] + cfg.gallery_mesh_origin_x
            y2 = b[1] + cfg.gallery_mesh_origin_y
            z2 = b[2] + cfg.gallery_mesh_origin_z

            x1t, y1t, z1t = svt.transform(x1, y1, z1, nd)
            x2t, y2t, z2t = svt.transform(x2, y2, z2, nd)

            line = QtWidgets.QGraphicsLineItem(x1t, y1t, x2t, y2t)
            line.setZValue(-80)
            line.setPen(pen)
            self._scene.addItem(line)
            self._scene.gallery_mesh_lines.append(line)
            self._scene.gallery_mesh_pos_list.append((x1, y1, z1, x2, y2, z2))

        for data in mesh.elements.values():
            type_, tags, nodeIDs = data
            if type_ != 2:
                continue
            a = nodeIDs[0]
            b = nodeIDs[1]
            c = nodeIDs[2]

            add_line(a, b)
            add_line(b, c)
            add_line(c, a)

    def hide_gallery_mesh(self):
        for item in self._scene.gallery_mesh_lines:
            self._scene.removeItem(item)
        self._scene.gallery_mesh_lines.clear()
        self._scene.gallery_mesh_pos_list.clear()

    def update_gallery_mesh_pos(self):
        svt = self.diagram_view._scene.side_view_tool
        nd = svt.dir_vec / np.linalg.norm(svt.dir_vec)

        for i in range(len(self._scene.gallery_mesh_lines)):
            gpt = self._scene.gallery_mesh_lines[i]
            pos = self._scene.gallery_mesh_pos_list[i]
            x1t, y1t, z1t = svt.transform(pos[0], pos[1], pos[2], nd)
            x2t, y2t, z2t = svt.transform(pos[3], pos[4], pos[5], nd)
            gpt.setLine(x1t, y1t, x2t, y2t)
            gpt.setVisible(z1t >= 0 and z2t >= 0)

    def update_pos(self):
        self.update_electrodes_pos()
        self.update_point_cloud_pos()
        self.update_gallery_mesh_pos()

    def wheelEvent(self, event):
        self.diagram_view.no_scroll = True

        if event.angleDelta().y() > 0:
            factor = 1.25
        else:
            factor = 0.8
        self.scale(factor, factor)

        self.diagram_view.save_y_center()
        self.diagram_view.setTransform(self.transform())

        self.diagram_view.no_scroll = False

    def scrollContentsBy(self, dx, dy):
        super().scrollContentsBy(dx, dy)
        if not self.no_scroll:
            no_scroll = self.diagram_view.no_scroll
            self.diagram_view.no_scroll = True
            scx = self.mapToScene(self.viewport().geometry().center()).x()
            #dcy = self.diagram_view.mapToScene(self.diagram_view.viewport().geometry().center()).y()
            self.diagram_view.centerOn(scx, self.diagram_view.y_center)
            self.diagram_view.no_scroll = no_scroll

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.diagram_view.save_y_center()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.save_y_center()

    def save_y_center(self):
        self.y_center = self.mapToScene(self.viewport().geometry().center()).y()


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Cursor.setup_cursors()
    mainWindow = DiagramView()
    mainWindow.setGeometry(500, 300, 800, 600)
    mainWindow.show()
    sys.exit(app.exec_())
