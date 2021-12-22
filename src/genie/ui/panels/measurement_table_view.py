from PyQt5 import QtWidgets, QtCore, QtGui

from genie.core.global_const import GenieMethod
from genie.core import misc
from genie.core import ert_prepare
from genie.core.data_types import MeasurementsModelInfo
from genie.core.icons_dir import icons_dir

import math
import os
import json


class Meas:
    def __init__(self, meas, electrode_groups):
        self._meas = meas
        self._electrode_groups = electrode_groups

        self.d = meas.data["data"]
        self.size = self.d.shape[0]
        self.app_res_gimli = None

    def get_app_res_gimli(self):
        if self.app_res_gimli is None:
            data, meas_info = ert_prepare.prepare(self._electrode_groups, [self._meas])
            k = misc.geometricFactors(data)
            self.app_res_gimli = []
            for i in range(self.size):
                self.app_res_gimli.append(self.d["V"][i] / self.d["I"][i] * k[i])
        return self.app_res_gimli


class MeasurementTableModel(QtCore.QAbstractItemModel):
    def __init__(self, electrode_groups, measurements, genie, parent=None):
        super().__init__(parent)

        self._electrode_groups = electrode_groups
        self._measurements = measurements
        self.genie = genie

        self.model_map = {}
        self.update_model_data()

        self.meas_list = []
        for m in self._measurements:
            if m.data is not None:
                self.meas_list.append(Meas(m, electrode_groups))

        self._num_rows = sum([m.size for m in self.meas_list])

        self._masked = [False] * self._num_rows

        self.row_meas_line_map = {r: self.row_to_meas_line(r) for r in range(self._num_rows)}

        self.red_brush = QtGui.QBrush(QtGui.QColor("red"), QtCore.Qt.SolidPattern)

    def update_model_data(self):
        if self.genie.project_cfg is not None:
            file_name = os.path.join(self.genie.cfg.current_project_dir, "inversions",
                                     self.genie.project_cfg.curren_inversion_name, "measurements_model_info.json")
            if os.path.isfile(file_name):
                with open(file_name) as fd:
                    meas_model_info = MeasurementsModelInfo.deserialize(json.load(fd))
                for item in meas_model_info.items:
                    self.model_map[(item.ca, item.cb, item.pa, item.pb)] = item

    def row_to_meas_line(self, row):
        meas_id = 0
        while row >= self.meas_list[meas_id].size:
            row -= self.meas_list[meas_id].size
            meas_id += 1
        return meas_id, row

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return QtCore.QVariant()

        def nan_str(x):
            if math.isnan(x):
                return ""
            return x

        def get_model_line(line):
            k = (d["ca"][line], d["cb"][line], d["pa"][line], d["pb"][line])
            if k in self.model_map:
                return self.model_map[k]
            return None

        if role == QtCore.Qt.DisplayRole:
            meas_id, line = self.row_meas_line_map[index.row()]
            if index.column() == 0:
                return QtCore.QVariant(self._measurements[meas_id].number)
            else:
                d = self.meas_list[meas_id].d
                if index.column() == 1:
                    return QtCore.QVariant(d["ca"][line])
                elif index.column() == 2:
                    return QtCore.QVariant(d["cb"][line])
                elif index.column() == 3:
                    return QtCore.QVariant(d["pa"][line])
                elif index.column() == 4:
                    return QtCore.QVariant(d["pb"][line])
                elif index.column() == 5:
                    return QtCore.QVariant(nan_str(float(d["I"][line])))
                elif index.column() == 6:
                    return QtCore.QVariant(nan_str(float(d["V"][line])))
                elif index.column() == 7:
                    return QtCore.QVariant(nan_str(float(d["AppRes"][line])))
                elif index.column() == 8:
                    return QtCore.QVariant(nan_str(float(d["std"][line])))
                elif index.column() == 9:
                    return QtCore.QVariant(nan_str(float(self.meas_list[meas_id].get_app_res_gimli()[line])))
                elif index.column() == 10:
                    ml = get_model_line(line)
                    if ml is not None:
                        return QtCore.QVariant(float(ml.app_res_model))
                    else:
                        return QtCore.QVariant("")
                elif index.column() == 11:
                    ml = get_model_line(line)
                    if ml is not None:
                        return QtCore.QVariant(float(ml.app_res_model / d["AppRes"][line]))
                    else:
                        return QtCore.QVariant("")
                elif index.column() == 12:
                    ml = get_model_line(line)
                    if ml is not None:
                        return QtCore.QVariant(float(ml.app_res_start_model))
                    else:
                        return QtCore.QVariant("")
                elif index.column() == 13:
                    ml = get_model_line(line)
                    if ml is not None:
                        return QtCore.QVariant(float(ml.app_res_start_model / d["AppRes"][line]))
                    else:
                        return QtCore.QVariant("")
                else:
                    return QtCore.QVariant("")

        elif role == QtCore.Qt.ForegroundRole:
            meas_id, line = self.row_meas_line_map[index.row()]
            AppResGimli = self.meas_list[meas_id].get_app_res_gimli()[line]
            if AppResGimli <= 1e-12 or math.isnan(AppResGimli):
                return QtCore.QVariant(self.red_brush)
            else:
                return QtCore.QVariant()

        elif role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                if self._masked[index.row()]:
                    return QtCore.QVariant(QtCore.Qt.Checked)
                else:
                    return QtCore.QVariant(QtCore.Qt.Unchecked)

        return QtCore.QVariant()

    def setData(self, index, value, role):
        if index.isValid() and role == QtCore.Qt.CheckStateRole:
            self._masked[index.row()] = (value == QtCore.Qt.Checked)
            self.dataChanged.emit(index, index, [role])
            return True

        return False

    def flags(self, index):
        if not index.isValid():
            return 0

        if index.column() == 0:
            return super().flags(index) | QtCore.Qt.ItemIsUserCheckable
        else:
            return super().flags(index)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if parent.isValid():
            return QtCore.QModelIndex()
        else:
            return self.createIndex(row, column)

    def parent(self, index):
        return QtCore.QModelIndex()

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return self._num_rows

    def columnCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return 14

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        headers = ["meas_number", "ca", "cb", "pa", "pb", "I[A]", "V[V]", "AppRes[Ohmm]", "std", "AppResGimli[Ohmm]", "AppResModel[Ohmm]", "ratio", "AppResStartModel[Ohmm]", "start_ratio"]

        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole and section < len(headers):
            return QtCore.QVariant(headers[section])

        return QtCore.QVariant()

    def maskedMeasLines(self):
        ret = {}
        row = 0
        for i, m in enumerate(self.meas_list):
            l = []
            for j in range(m.size):
                l.append(self._masked[row])
                row += 1
            ret[self._measurements[i].number] = l

        return ret

    def maskMeasLines(self, data):
        for row in range(self._num_rows):
            meas_id, line = self.row_meas_line_map[row]
            number = self._measurements[meas_id].number
            if number in data and line < len(data[number]):
                self._masked[row] = data[number][line]
            else:
                self._masked[row] = False


class ProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self):
        super().__init__()

        self.checked_meas = []
        self.mins = [None] * 9
        self.maxs = [None] * 9

    def filterAcceptsRow(self, sourceRow, sourceParent):
        if not self.filterNumer(sourceRow, sourceParent):
            return False

        if not self.filterQuantity(sourceRow, sourceParent):
            return False

        return True

    def filterNumer(self, sourceRow, sourceParent):
        index_number = self.sourceModel().index(sourceRow, 0, sourceParent)
        if self.sourceModel().data(index_number) not in self.checked_meas:
            return False
        return True

    def filterQuantity(self, sourceRow, sourceParent):
        def get_data(i):
            index = self.sourceModel().index(sourceRow, i + 5, sourceParent)
            return self.sourceModel().data(index)

        for i in range(len(self.mins)):
            data = None
            if self.mins[i] is not None:
                data = get_data(i)
                if data == "" or data < self.mins[i]:
                    return False
            if self.maxs[i] is not None:
                if data is None:
                    data = get_data(i)
                if data == "" or data > self.maxs[i]:
                    return False

        return True

    def lessThan(self, left, right):
        leftData = self.sourceModel().data(left)
        rightData = self.sourceModel().data(right)

        if leftData == "":
            return False

        if rightData == "":
            return True

        return super().lessThan(left, right)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.BackgroundRole and 4 < section < 14:
            ind = section - 5
            if (self.mins[ind] is not None) or (self.maxs[ind] is not None):
                return QtCore.QVariant(QtGui.QBrush(QtGui.QColor("orange"), QtCore.Qt.SolidPattern))

        return super().headerData(section, orientation, role)


class MeasurementTableView(QtWidgets.QWidget):
    def __init__(self, main_window, model, parent=None):
        super().__init__(parent)

        self.genie = main_window.genie

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.view = QtWidgets.QTreeView(self)
        layout.addWidget(self.view)

        self.filter_model = ProxyModel()
        self.filter_model.setSourceModel(model)

        self.view.setRootIsDecorated(False)
        self.view.setModel(self.filter_model)
        self.view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.reset_sort()
        self.view.setSortingEnabled(True)
        self.view.header().setSectionsMovable(False)

        self.view.header().resizeSection(1, 40)
        self.view.header().resizeSection(2, 40)
        self.view.header().resizeSection(3, 40)
        self.view.header().resizeSection(4, 40)

        icon_file = os.path.join(icons_dir, "cross.png")
        self.view.setStyleSheet(
            "QTreeView::indicator:checked {image: url(" + icon_file + ");}"
        )

        self.action_select_all = QtWidgets.QAction("Select all")
        self.action_mask = QtWidgets.QAction("Mask")
        self.action_unmask = QtWidgets.QAction("Unmask")
        self.action_reset_sort = QtWidgets.QAction("Reset sort")
        self.action_save_csv = QtWidgets.QAction("Save as csv...")

        self.action_select_all.triggered.connect(self.select_all)
        self.action_mask.triggered.connect(self.mask)
        self.action_unmask.triggered.connect(self.unmask)
        self.action_reset_sort.triggered.connect(self.reset_sort)
        self.action_save_csv.triggered.connect(self.save_csv)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        menu.addAction(self.action_select_all)
        menu.addAction(self.action_mask)
        menu.addAction(self.action_unmask)
        menu.addSeparator()
        menu.addAction(self.action_reset_sort)
        menu.addSeparator()
        menu.addAction(self.action_save_csv)
        menu.exec(event.globalPos())

    def select_all(self):
        row_count = self.filter_model.rowCount()
        column_count = self.filter_model.columnCount()
        topLeft = self.filter_model.index(0, 0)
        bottomRight = self.filter_model.index(row_count - 1, column_count - 1)
        selection = QtCore.QItemSelection(topLeft, bottomRight)
        self.view.selectionModel().select(selection, QtCore.QItemSelectionModel.Select)

    def mask(self):
        sm = self.view.selectionModel()
        rows = [r.row() for r in sm.selectedRows()]
        for r in rows:
            self.filter_model.setData(self.filter_model.index(r, 0), QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)

    def unmask(self):
        sm = self.view.selectionModel()
        rows = [r.row() for r in sm.selectedRows()]
        for r in rows:
            self.filter_model.setData(self.filter_model.index(r, 0), QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

    def reset_sort(self):
        self.view.sortByColumn(-1, QtCore.Qt.AscendingOrder)

    def save_csv(self):
        dir = self.genie.cfg.current_project_dir
        file = QtWidgets.QFileDialog.getSaveFileName(self, "Save table to file",
                                                     os.path.join(dir, "table.csv"),
                                                     "CSV (*.csv)")
        file_name = file[0]
        if file_name:
            col = self.filter_model.columnCount()
            row = self.filter_model.rowCount()
            with open(file_name, "w") as fd:
                for i in range(col):
                    fd.write(self.filter_model.headerData(i, QtCore.Qt.Horizontal))
                    if i < col - 1:
                        fd.write(',')
                fd.write('\n')

                for i in range(row):
                    for j in range(col):
                        fd.write(str(self.filter_model.data(self.filter_model.index(i, j))))
                        if j < col - 1:
                            fd.write(',')
                    fd.write('\n')
