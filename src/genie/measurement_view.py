from PyQt5 import QtWidgets, QtCore, QtGui


class MeasurementModel(QtCore.QAbstractItemModel):
    def __init__(self, measurements, parent=None):
        super().__init__(parent)

        self._measurements = measurements
        self._checked = [False] * len(measurements)

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()

        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return QtCore.QVariant(self._measurements[index.row()].number)
            elif index.column() == 1:
                return QtCore.QVariant(self._measurements[index.row()].file)

        elif role == QtCore.Qt.CheckStateRole:
            if index.column() == 0:
                if self._checked[index.row()]:
                    return QtCore.QVariant(QtCore.Qt.Checked)
                else:
                    return QtCore.QVariant(QtCore.Qt.Unchecked)

        return QtCore.QVariant()

    def setData(self, index, value, role):
        if index.isValid() and role == QtCore.Qt.CheckStateRole:
            self._checked[index.row()] = (value == QtCore.Qt.Checked)
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
            return len(self._measurements)

    def columnCount(self, parent=QtCore.QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return 2

    def headerData(self, section, orientation, role):
        headers = ["Number", "File"]

        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole and section < len(headers):
            return QtCore.QVariant(headers[section])

        return QtCore.QVariant()

    def checkedMeasurements(self):
        return [self._measurements[i] for i in range(len(self._measurements)) if self._checked[i]]


class MeasurementView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setRootIsDecorated(False)
        #self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
