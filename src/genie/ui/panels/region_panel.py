from ..dialogs.add_region_dialog import AddRegionDlg

from PyQt5 import QtWidgets, QtCore, QtGui

from contextlib import contextmanager


@contextmanager
def nosignal(qt_obj):
    """
    Context manager for blocking signals inside some signal handlers.
    """
    qt_obj.blockSignals(True)
    yield qt_obj
    qt_obj.blockSignals(False)


class RegionPanel(QtWidgets.QWidget):
    region_changed = QtCore.pyqtSignal(int)
    # current region in current tab has changed

    def __init__(self, parent, diagram):
        super().__init__(parent)

        self._diagram = diagram

        self._region_id = 0

        self._combo_id_to_idx = {0: 0}
        # auxiliary map from region ID to index in the combo box.

        self._make_widgets()

    def _make_widgets(self):
        """Make grid of widgets of the single region tab.
           Do not fill the content.
        """
        grid = QtWidgets.QGridLayout()


        self.wg_region_combo = QtWidgets.QComboBox()
        self.wg_region_combo.currentIndexChanged.connect(self._combo_set_region)
        grid.addWidget(self.wg_region_combo, 0, 0)

        self.wg_add_button = QtWidgets.QPushButton("+")
        #self.wg_add_button.setIcon(icon.get_app_icon("add"))
        self.wg_add_button.setToolTip('Create new region')
        self.wg_add_button.clicked.connect(self.add_region)
        grid.addWidget(self.wg_add_button, 0, 1)

        self.wg_remove_button = QtWidgets.QPushButton("-")
        #self.wg_remove_button.setIcon(icon.get_app_icon("remove"))
        self.wg_remove_button.clicked.connect(self.remove_region)
        grid.addWidget(self.wg_remove_button, 0, 2)

        # name
        self.wg_name = QtWidgets.QLineEdit()
        self.wg_name.editingFinished.connect(self._name_editing_finished)
        grid.addWidget(self.wg_name, 1, 1, 1, 2)
        name_label = QtWidgets.QLabel("Name:", self)
        name_label.setToolTip("Name of the region.")
        name_label.setBuddy(self.wg_name)
        grid.addWidget(name_label, 1, 0)

        # color button
        self.wg_color_button = QtWidgets.QPushButton()
        self.wg_color_button.setFixedSize(25, 25)
        self.wg_color_button.clicked.connect(self._set_color)
        grid.addWidget(self.wg_color_button, 2, 1)
        color_label = QtWidgets.QLabel("Color:", self)
        color_label.setBuddy(self.wg_color_button)
        grid.addWidget(color_label, 2, 0)

        # dimension (just label)
        wg_dim_label = QtWidgets.QLabel("Dimension:", self)
        grid.addWidget(wg_dim_label, 3, 0)
        self.wg_dims = QtWidgets.QLabel("", self)
        grid.addWidget(self.wg_dims, 3, 1)

        self.setLayout(grid)
        self.setFixedHeight(self.minimumSizeHint().height())

    def _update_region_list(self):
        """
        Update combobox according to the region list.
        :return:
        """
        with nosignal(self.wg_region_combo) as combo:
            # self.wg_region_combo.setUpdatesEnabled(False) # Disable repainting until combobox is filled.
            combo.clear()
            self._combo_id_to_idx = {}
            sorted_regions = self._diagram.regions.regions.values()
            for idx, reg in enumerate(sorted_regions):
                print(idx, reg)
                self._combo_id_to_idx[reg.id] = idx
                combo.addItem(self.make_combo_label(reg), reg.id)
            # self.wg_region_combo.setUpdatesEnabled(True)
        self._region_id = 0
        self._update_region_content()

    def make_combo_label(self, region):
        """Region label for the combo box."""
        return region.name + " (" + AddRegionDlg.REGION_DESCRIPTION_DIM[region.dim] + ")"

    def _update_region_content(self, emit=True):
        """
        Update widgets according to selected region.
        :return:
        """
        with nosignal(self.wg_region_combo) as o:
            o.setCurrentIndex(self._combo_id_to_idx[self._region_id])

        if emit:
            self.region_changed.emit(self._region_id)

        region = self._diagram.regions.regions[self._region_id]

        is_default = self._region_id == 0
        if is_default:
            self.wg_remove_button.setEnabled(False)
            self.wg_remove_button.setToolTip('Default region cannot be removed!')
        elif self._diagram.regions.is_region_used(self._region_id):
            self.wg_remove_button.setEnabled(False)
            self.wg_remove_button.setToolTip('Region is still in use!')
        else:
            self.wg_remove_button.setEnabled(True)
            self.wg_remove_button.setToolTip('Remove selected region')

        self.wg_name.setText(region.name)

        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(QtGui.QColor(region.color))
        self.wg_color_button.setIcon(QtGui.QIcon(pixmap))

        self.wg_dims.setText(AddRegionDlg.REGION_DESCRIPTION_DIM[region.dim])

        none_widgets = [self.wg_color_button, self.wg_name]
        if is_default:
            for wg in none_widgets:
                wg.setEnabled(False)
        else:
            for wg in none_widgets:
                wg.setEnabled(True)

    def add_region(self):
        dialog = AddRegionDlg(3, self._diagram.regions.get_region_names(), self)
        dialog_result = dialog.exec_()
        if dialog_result == QtWidgets.QDialog.Accepted:
            name = dialog.region_name.text()
            dim = dialog.region_dim.currentData()
            reg_id = self._diagram.regions.add_region(name=name, dim=dim)

            self._diagram.selection.deselect_all(emit=False)

            self._update_region_list()
            self._combo_set_region(self._combo_id_to_idx[reg_id])

    def remove_region(self):
        """Remove the region."""
        if not self._diagram.regions.is_region_used(self._region_id):
            self._diagram.regions.delete_region(self._region_id)

            self._diagram.selection.deselect_all(emit=False)

            self._update_region_list()
        else:
            print("List is not empty! Oops, this button should have been disabled.")

    # ======= Internal signal handlers
    def _combo_set_region(self, idx):
        """
        Handle change in region combo box.
        """
        self._region_id = self.wg_region_combo.itemData(idx)
        self._update_region_content()

    def _name_editing_finished(self):
        """
        Handler of region name change.
        :return:
        """
        region = self._diagram.regions.regions[self._region_id]
        new_name = self.wg_name.text().strip()
        reg = None
        for r in self._diagram.regions.regions.values():
            if new_name == r.name:
                reg = r
                break
        if reg and reg.id != region.id:
            error = "Region name already exist"
        elif not new_name:
            error = "Region name is empty"
        else:
            error = None
            region.name = new_name

        if error:
            # err_dialog = GMErrorDialog(self)
            # err_dialog.open_error_dialog(error)
            print("Error")
            self.wg_name.selectAll()

        r = self._region_id
        self._update_region_list()
        self._region_id = r
        self._update_region_content()

    def _set_color(self):
        """Region color is changed, refresh diagram"""
        color_dialog = QtWidgets.QColorDialog(QtGui.QColor(self._diagram.regions.regions[self._region_id].color))
        for icol, color in enumerate(AddRegionDlg.BACKGROUND_COLORS):
            color_dialog.setCustomColor(icol, color)
        selected_color = color_dialog.getColor()

        if selected_color.isValid():
            self._diagram.regions.regions[self._region_id].color = selected_color.name()

        self._update_region_content()
        self._diagram.selection.deselect_all(emit=False)
        self.region_changed.emit(self._region_id)

    def selection_changed(self):
        self._region_id = self._diagram.regions.get_common_region()
        self._update_region_content(emit=False)
