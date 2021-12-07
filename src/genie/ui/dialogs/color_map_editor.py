import glob
import json
import math
import os
import sys
from pathlib import Path
from shutil import copyfile

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QPixmap, QPainter, QLinearGradient, QColor, QImage, qAlpha, qRed, qGreen, qBlue, QTransform
from PyQt5.QtWidgets import QDialog, QWidget, QLabel, QApplication, QHBoxLayout, QListWidget, QListWidgetItem, QLayout, \
    QVBoxLayout, QDialogButtonBox, QPushButton, QFileDialog
from vtkmodules.vtkCommonCore import vtkLookupTable

class ColorMapPreset(QWidget):
    def __init__(self, color_data_filename, user_defined=None):
        super(ColorMapPreset, self).__init__()
        self.color_data_filename = color_data_filename
        with open(color_data_filename, 'r') as file:
            color_data = json.load(file)
        self.values = list(color_data[0]["RGBPoints"][::4])
        self.colors = list(zip(color_data[0]["RGBPoints"][1::4],
                               color_data[0]["RGBPoints"][2::4],
                               color_data[0]["RGBPoints"][3::4]))

        layout = QHBoxLayout()
        self.bar = QLabel()
        layout.addWidget(self.bar)
        self.bar.setPixmap(self.create_pixmap())

        self.name = QLabel(color_data[0]["Name"])
        font = self.name.font()
        font.setBold(True)
        font.setPointSize(9)
        font.setUnderline(True)
        self.name.setFont(font)
        layout.addWidget(self.name)
        layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(layout)

        self.user_defined = user_defined

    def create_pixmap(self, pixmap_height=20, minimum=None, maximum=None):
        #doesnt yet work with linear scale
        if minimum is None:
            minimum = self.values[0]
            maximum = self.values[-1]


        orig_range = self.values[-1] - self.values[0]
        new_range = maximum - minimum

        pixmap = QPixmap(200, pixmap_height)
        pixmap.fill(Qt.magenta)
        painter = QPainter()
        painter.begin(pixmap)
        if len(self.values) == 1:
            painter.fillRect(0, 0, 200, pixmap_height, QColor(self.colors[0] * 255,
                                                              self.colors[1] * 255,
                                                              self.colors[2] * 255))
        else:
            if minimum == maximum:
                zoom = 1000
            else:
                zoom = min(orig_range/new_range, 100)

            gradient = QLinearGradient(QPoint(-(minimum - self.values[0]) * 200 * zoom,
                                              math.ceil(pixmap_height/2)),
                                       QPoint(200 * zoom - (minimum - self.values[0]) * 200 * zoom,
                                              math.ceil(pixmap_height/2)))
            range_start = self.values[0]
            range_length = self.values[-1] - self.values[0]
            colors = self.colors.__iter__()
            for value in self.values:
                pos = (value - range_start) / range_length
                color = next(colors)
                gradient.setColorAt(pos, QColor(color[0] * 255, color[1] * 255, color[2] * 255))

            painter.fillRect(0, 0, 200, pixmap_height, gradient)

        painter.end()
        return pixmap

    @staticmethod
    def copy_lut_settings(src_lut, dest_lut):
        dest_lut.SetRamp(src_lut.GetRamp())
        dest_lut.SetRange(src_lut.GetRange())
        dest_lut.SetScale(src_lut.GetScale())

    def make_new_lut(self, lut, pixmap=None):
        new_lut = vtkLookupTable()
        self.copy_lut_settings(lut, new_lut)
        new_lut.SetNumberOfTableValues(200)
        if pixmap == None:
            map = QImage(self.bar.pixmap())
        else:
            map = QImage(pixmap)
        for index in range(200):
            pixel = map.pixel(index, 0)
            new_lut.SetTableValue(index, qRed(pixel) / 255, qGreen(pixel) / 255, qBlue(pixel) / 255, 1)

        new_lut.Build()
        return new_lut

    @staticmethod
    def use_colormap(filename, lut):
        preset = ColorMapPreset(filename)
        new_lut = preset.make_new_lut(lut)
        lut.DeepCopy(new_lut)

    @staticmethod
    def use_colormap_linked(filename, lut, min, max):
        preset = ColorMapPreset(filename)
        pixmap = preset.create_pixmap(1, min, max)
        new_lut = preset.make_new_lut(lut, pixmap)
        new_lut.SetRange(min, max)
        lut.DeepCopy(new_lut)


class ColorMapEditor(QDialog):
    def __init__(self, genie):
        super(ColorMapEditor, self).__init__()
        self.setWindowTitle("Colormap Presets")
        self.resize(640, 480)
        self.genie = genie
        layout = QVBoxLayout()
        self.list = QListWidget()
        layout.addWidget(self.list)

        for filename in glob.glob(os.path.realpath(os.path.join(genie.COLORMAPS_DIR, "*.json"))):
            self.add_preset(filename, user_defined=False)

        for filename in glob.glob(os.path.join(self.genie.cfg.current_project_dir, "color_maps", "*.json")):
            self.add_preset(filename, 0, user_defined=True)

        self.list.item(0).setSelected(True)

        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        import_button = QPushButton("Import...")
        buttons.addButton(import_button, QDialogButtonBox.ActionRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        import_button.clicked.connect(self.import_preset)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.list.focusWidget()

    def set_new_lut(self, lut):
        colormap_item = self.list.selectedItems()[0]
        colormap_widget = self.list.itemWidget(colormap_item)
        new_lut = colormap_widget.make_new_lut(lut)
        lut.DeepCopy(new_lut)

        if colormap_widget.user_defined:
            #user defined color map
            filename = os.path.relpath(colormap_widget.color_data_filename, self.genie.cfg.current_project_dir)
        else:
            #default color maps
            filename = os.path.relpath(colormap_widget.color_data_filename, self.genie.COLORMAPS_DIR)

        self.genie.current_inversion_cfg.colormap_file = os.path.normpath(filename)

    def add_preset(self, abs_filename,  index=None, user_defined=False):
        widget = ColorMapPreset(abs_filename, user_defined)
        names = [self.list.itemWidget(self.list.item(index)).name.text() for index in range(self.list.count())]
        name_extension = 1
        original_name = widget.name.text()
        while widget.name.text() in names:
            widget.name.setText(original_name + f"_{name_extension}")
            name_extension += 1

        item = QListWidgetItem()
        self.list.insertItem(index if index is not None else self.list.count(), item)

        item.setSizeHint(widget.sizeHint())
        self.list.setItemWidget(item, widget)

        return widget

    def import_preset(self):
        filename = QFileDialog.getOpenFileName(self,
                                               "Import Colormap",
                                               self.genie.cfg.last_colormap_dir,
                                               "Colormap file (*.json)")[0]
        if filename:
            self.genie.cfg.last_colormap_dir = os.path.dirname(filename)
            colormap_dir = os.path.join(self.genie.cfg.current_project_dir, "color_maps")
            Path(colormap_dir).mkdir(parents=True, exist_ok=True)
            dest_file = os.path.join(colormap_dir, os.path.split(filename)[1])
            index = 1
            while os.path.exists(dest_file):
                root, ext = os.path.splitext(dest_file)
                dest_file = root + f"_{index}" + ext
                index += 1
            copyfile(filename, dest_file)
            self.add_preset(os.path.relpath(dest_file), 0, user_defined=True)
