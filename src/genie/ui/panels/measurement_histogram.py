from PyQt5 import QtWidgets, QtCore, QtGui

from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure

import numpy as np

from genie.core.global_const import GenieMethod
from .mesh_cut_tool_panel import MeshCutToolPanelEdit

import os


class ComboData:
    def __init__(self, name, col, unit):
        self.name = name
        self.col = col
        self.unit = unit


class DoubleValidatorEmpty(QtGui.QDoubleValidator):
    def validate(self, input, pos):
        if input == "":
            return (QtGui.QValidator.Acceptable, input, pos)
        return super().validate(input, pos)


class MeasurementHistogram(QtWidgets.QWidget):
    def __init__(self, main_window, meas_table_view, parent=None):
        super().__init__(parent)

        self.genie = main_window.genie
        self.meas_table_view = meas_table_view

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.canvas = FigureCanvas(Figure())
        self.canvas.figure.subplots_adjust(left=0.075, right=0.95, top=0.95, bottom=0.075)
        layout.addWidget(self.canvas)

        self._static_ax = self.canvas.figure.subplots()

        lay = QtWidgets.QHBoxLayout()
        lay.addWidget(QtWidgets.QLabel("Logaritmic X axis:"))
        self._log_checkbox = QtWidgets.QCheckBox()
        self._log_checkbox.stateChanged.connect(self.show_hist)
        lay.addWidget(self._log_checkbox)
        lay.addStretch()
        layout.addLayout(lay)

        self.combo_data = self.create_combo_data()
        self.current_combo_data = self.combo_data[0]
        self.last_combo_data = None

        lay = QtWidgets.QHBoxLayout()
        lay.addWidget(QtWidgets.QLabel("Quantity:"))
        self._histComboBox = QtWidgets.QComboBox()
        for d in self.combo_data:
            self._histComboBox.addItem(d.name, d)
        self._histComboBox.currentTextChanged.connect(self.combo_change)
        lay.addWidget(self._histComboBox)
        lay.addStretch()
        layout.addLayout(lay)

        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(QtWidgets.QLabel("Filter: min:"))
        self.filter_min_edit = MeshCutToolPanelEdit(self.filter_edit_finished)
        self.filter_min_edit.setValidator(DoubleValidatorEmpty())
        self.filter_min_edit.setMaximumWidth(100)
        filter_layout.addWidget(self.filter_min_edit)
        filter_layout.addWidget(QtWidgets.QLabel("max:"))
        self.filter_max_edit = MeshCutToolPanelEdit(self.filter_edit_finished)
        self.filter_max_edit.setValidator(DoubleValidatorEmpty())
        self.filter_max_edit.setMaximumWidth(100)
        filter_layout.addWidget(self.filter_max_edit)
        self.reset_filterButton = QtWidgets.QPushButton("Reset filter")
        self.reset_filterButton.clicked.connect(self.reset_filter_handle)
        filter_layout.addWidget(self.reset_filterButton)
        self.reset_all_filtersButton = QtWidgets.QPushButton("Reset all filters")
        self.reset_all_filtersButton.clicked.connect(self.reset_all_filters_handle)
        filter_layout.addWidget(self.reset_all_filtersButton)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        lay = QtWidgets.QHBoxLayout()
        self.mask_outsideButton = QtWidgets.QPushButton("Mask values outside filters")
        self.mask_outsideButton.clicked.connect(self.mask_outside_handle)
        lay.addWidget(self.mask_outsideButton)
        lay.addStretch()
        layout.addLayout(lay)

        lay = QtWidgets.QHBoxLayout()
        self.save_pdfButton = QtWidgets.QPushButton("Save as pdf...")
        self.save_pdfButton.clicked.connect(self.save_pdf)
        lay.addWidget(self.save_pdfButton)
        lay.addStretch()
        layout.addLayout(lay)

        self.show_hist()

    def combo_change(self):
        self.last_combo_data = self.current_combo_data
        self.current_combo_data = self._histComboBox.currentData()

        self.show_hist()
        self.update_edits()

    def show_hist(self):
        self._static_ax.cla()

        rows = self.meas_table_view.filter_model.rowCount()

        if self.last_combo_data and (self.last_combo_data is not self.current_combo_data) and \
                (self.last_combo_data.unit == self.current_combo_data.unit):
            v = []
            for i in range(rows):
                v.append(self.meas_table_view.filter_model.data(self.meas_table_view.filter_model.index(i, self.last_combo_data.col)))
            self.print_line(v, "gray")

        v = []
        for i in range(rows):
            v.append(self.meas_table_view.filter_model.data(self.meas_table_view.filter_model.index(i, self.current_combo_data.col)))
        self.print_line(v)

        self.canvas.draw_idle()

    def print_line(self, data, color=None):
        if self._log_checkbox.isChecked() and data:
            data = [d for d in data if d != "" and d > 1e-12]
            bins = 10 ** np.linspace(np.floor(np.log10(min(data))), np.ceil(np.log10(max(data))), 100)
            self._static_ax.set_xscale('log')
        else:
            data = [d for d in data if d != ""]
            bins = 100
            self._static_ax.set_xscale('linear')

        if data:
            self._static_ax.hist(data, bins, histtype='step', color=color)

    def update_edits(self):
        ind = self._histComboBox.currentIndex()
        min = self.meas_table_view.filter_model.mins[ind]
        max = self.meas_table_view.filter_model.maxs[ind]
        self.filter_min_edit.setText(str(min) if min is not None else "")
        self.filter_max_edit.setText(str(max) if max is not None else "")

    def create_combo_data(self):
        ret = []

        d = ComboData("I", 5, "A")
        ret.append(d)

        d = ComboData("V", 6, "V")
        ret.append(d)

        d = ComboData("AppRes", 7, "Ohmm")
        ret.append(d)

        d = ComboData("std", 8, "")
        ret.append(d)

        d = ComboData("AppResGimli", 9, "Ohmm")
        ret.append(d)

        d = ComboData("AppResModel", 10, "Ohmm")
        ret.append(d)

        d = ComboData("ratio", 11, "")
        ret.append(d)

        d = ComboData("AppResStartModel", 12, "Ohmm")
        ret.append(d)

        d = ComboData("start_ratio", 13, "")
        ret.append(d)

        return ret

    def filter_edit_finished(self):
        def float_none(s):
            try:
                return float(s)
            except ValueError:
                return None

        ind = self._histComboBox.currentIndex()

        self.meas_table_view.filter_model.mins[ind] = float_none(self.filter_min_edit.text())
        self.meas_table_view.filter_model.maxs[ind] = float_none(self.filter_max_edit.text())

        self.meas_table_view.filter_model.invalidateFilter()
        self.show_hist()

    def reset_filter_handle(self):
        ind = self._histComboBox.currentIndex()

        self.meas_table_view.filter_model.mins[ind] = None
        self.meas_table_view.filter_model.maxs[ind] = None

        self.meas_table_view.filter_model.invalidateFilter()
        self.show_hist()
        self.update_edits()

    def reset_all_filters_handle(self):
        self.meas_table_view.filter_model.mins = [None] * 9
        self.meas_table_view.filter_model.maxs = [None] * 9

        self.meas_table_view.filter_model.invalidateFilter()
        self.show_hist()
        self.update_edits()

    def mask_outside_handle(self):
        row_count = self.meas_table_view.filter_model.sourceModel().rowCount()
        for row in range(row_count):
            if not self.meas_table_view.filter_model.filterNumer(row, QtCore.QModelIndex()):
                continue

            if not self.meas_table_view.filter_model.filterQuantity(row, QtCore.QModelIndex()):
                self.meas_table_view.filter_model.sourceModel().setData(
                    self.meas_table_view.filter_model.sourceModel().index(row, 0), QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)

    def save_pdf(self):
        dir = self.genie.cfg.current_project_dir
        file = QtWidgets.QFileDialog.getSaveFileName(self, "Save histogram to file",
                                                     os.path.join(dir, "hist.pdf"),
                                                     "PDF (*.pdf)")
        file_name = file[0]
        if file_name:
            self.canvas.figure.savefig(file_name)
