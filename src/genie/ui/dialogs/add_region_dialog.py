"""
Dialog for adding region to interface.
"""
#from gm_base.geometry_files.format_last import RegionDim
import PyQt5.QtWidgets as QtWidgets
import PyQt5.QtGui as QtGui
#from gm_base.geomop_dialogs import GMErrorDialog
#import gm_base.icon as icon

import enum


class RegionDim(enum.IntEnum):
    invalid = -2
    none = -1
    point = 0
    well = 1
    fracture = 2
    bulk = 3


class AddRegionDlg(QtWidgets.QDialog):
    BACKGROUND_COLORS = [
        QtGui.QColor("#ff0000"),  # red
        QtGui.QColor("#ffff00"),  # yellow
        QtGui.QColor("#00ff00"),  # lime
        QtGui.QColor("#00ffff"),  # aqua
        QtGui.QColor("#0000ff"),  # blue
        QtGui.QColor("#ff00ff"),  # fuchsia
        QtGui.QColor("#800000"),  # maroon
        QtGui.QColor("#808000"),  # olive
        QtGui.QColor("#008000"),  # green
        QtGui.QColor("#008080"),  # teal
        QtGui.QColor("#000080"),  # navy
        QtGui.QColor("#800080"),  # purple

        # QtGui.QColor("#e2caff"),  # blue1
        # QtGui.QColor("#bbffc0"),  # green1
        # QtGui.QColor("#fffaae"),  # yelow1
        # QtGui.QColor("#ffd3d0"),  # red1
        # QtGui.QColor("#c8c8c8"),  # gray
        # QtGui.QColor("#c1cfff"),  # blue2
        # QtGui.QColor("#ffcde6"),  # pink1
        # QtGui.QColor("#c1ffda"),  # green2
        # QtGui.QColor("#ffd0b8"),  # red2
        # QtGui.QColor("#ffff7f"),  # yelow2
        # QtGui.QColor("#ffd2f6"),  # pink2
        # QtGui.QColor("#cfebff"),  # blue3
        # QtGui.QColor("#e3ffb5"),  # green3
        # QtGui.QColor("#ffd7dd"),  # red3
        # QtGui.QColor("#f3ffb3"),  # yelow3
        # QtGui.QColor("#8effff")  # blue4
    ]

    # REGION_DESCRIPTION = {
    #     RegionDim.none: "None (default)",
    #     RegionDim.point: "Point (0D)",
    #     RegionDim.well: "Well (1D)",
    #     RegionDim.fracture: "Fracture (2D)",
    #     RegionDim.bulk: "Bulk (3D)"
    # }

    # REGION_DESCRIPTION_SHORT = {
    #     RegionDim.none: "default",
    #     RegionDim.point: "point",
    #     RegionDim.well: "well",
    #     RegionDim.fracture: "fracture",
    #     RegionDim.bulk: "bulk"
    # }


    # Usage: Add_region dialogue dropdown
    REGION_DESCRIPTION = {
        RegionDim.none: "Default (None)",
        RegionDim.point: "Point (0D)",
        RegionDim.well: "Edge (1D)",
        RegionDim.fracture: "Face (2D)",
        RegionDim.bulk: "Volume (3D)"
    }
    # Usage: Name suggestions in the dialogue
    REGION_DESCRIPTION_SHORT = {
        RegionDim.none: "default",
        RegionDim.point: "point",
        RegionDim.well: "edge",
        RegionDim.fracture: "face",
        RegionDim.bulk: "volume"
    }
    # Usage: Region panel dimension hints
    REGION_DESCRIPTION_DIM = {
        RegionDim.none: "None",
        RegionDim.point: "0D",
        RegionDim.well: "1D",
        RegionDim.fracture: "2D",
        RegionDim.bulk: "3D"
    }

    def __init__(self, init_dim, region_names, parent=None):
        super(AddRegionDlg, self).__init__(parent)
        self.region_names = region_names

        self.setWindowTitle("Add Region")

        grid = QtWidgets.QGridLayout(self)

        d_region_dim = QtWidgets.QLabel("Region Dimension:", self)
        self.region_dim = QtWidgets.QComboBox()
        self.region_dim.addItem(self.REGION_DESCRIPTION[RegionDim.point], RegionDim.point)
        self.region_dim.addItem(self.REGION_DESCRIPTION[RegionDim.well], RegionDim.well)
        self.region_dim.addItem(self.REGION_DESCRIPTION[RegionDim.fracture], RegionDim.fracture)
        self.region_dim.addItem(self.REGION_DESCRIPTION[RegionDim.bulk], RegionDim.bulk)

        self.region_dim.setCurrentIndex(init_dim)

        d_region_name = QtWidgets.QLabel("Region Name:", self)
        self.region_name = QtWidgets.QLineEdit()
        self.image = QtWidgets.QLabel(self)

        self.image.setMinimumWidth(self.region_name.sizeHint().height())

        #self.image.setPixmap(icon.get_app_icon("sign-check").pixmap(self.region_name.sizeHint().height()))
        self.image.setToolTip('Region name is unique, everything is fine.')
        self.have_default_name = True
        self.set_default_name(init_dim)
        self.region_name.textChanged.connect(self.reg_name_changed)

        grid.addWidget(d_region_name, 0, 0)
        grid.addWidget(self.region_name, 0, 1)
        grid.addWidget(self.image, 0, 2)

        self.region_dim.currentIndexChanged[int].connect(self.set_default_name)
        grid.addWidget(d_region_dim, 1, 0)
        grid.addWidget(self.region_dim, 1, 1, 1, 2)

        self._tranform_button = QtWidgets.QPushButton("Add", self)
        self._tranform_button.clicked.connect(self.accept)
        self._cancel_button = QtWidgets.QPushButton("Cancel", self)
        self._cancel_button.clicked.connect(self.reject)

        button_box = QtWidgets.QDialogButtonBox()
        button_box.addButton(self._tranform_button, QtWidgets.QDialogButtonBox.AcceptRole)
        button_box.addButton(self._cancel_button, QtWidgets.QDialogButtonBox.RejectRole)

        grid.addWidget(button_box, 2, 1)
        self.setLayout(grid)

    def is_unique_region_name(self, reg_name):
        """ Return False in the case of colision with an existing region name."""
        return reg_name not in self.region_names

    def reg_name_changed(self, reg_name):
        """ Called when Region Line Edit is changed."""
        self.have_default_name = False
        if self.is_unique_region_name(reg_name):
            # self.image.setPixmap(
            #     icon.get_app_icon("sign-check").pixmap(self.region_name.sizeHint().height())
            # )
            self.image.setToolTip('Unique name is OK.')
            self._tranform_button.setEnabled(True)
        else:
            # self.image.setPixmap(
            #     icon.get_app_icon("warning").pixmap(self.region_name.sizeHint().height())
            # )
            self.image.setToolTip('Name is not unique!')
            self._tranform_button.setEnabled(False)

    @classmethod
    def get_some_color(cls, i):
        """Return firs collor accoding to index"""
        return cls.BACKGROUND_COLORS[i % len(cls.BACKGROUND_COLORS)]

    def set_default_name(self, dim):
        """ Set default name if it seems to be default name. """
        if self.have_default_name:
            for reg_id in range(10000):
                name = "{}_{}".format(self.REGION_DESCRIPTION_SHORT[RegionDim(dim)], reg_id)
                if self.is_unique_region_name(name):
                    break
            self.region_name.setText(name)
            self.have_default_name = True

    def accept(self):
        """
        Accepts the form if region data is valid.
        :return: None
        """
        new_name = self.region_name.text()
        if not new_name.strip():
            error = "Region name is empty"
        elif new_name in self.region_names:
            error = "Region name already exist"
        else:
            error = None

        if error:
            #err_dialog = GMErrorDialog(self)
            #err_dialog.open_error_dialog(error)
            print("Error")
        else:
            super(AddRegionDlg, self).accept()
