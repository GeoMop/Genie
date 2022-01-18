"""
Dialog for editing first arrivals.
"""

from PyQt5 import QtCore, QtGui, QtWidgets

import numpy as np
import pyqtgraph as qtg


class FirstArrivalDlg(QtWidgets.QDialog):
    def __init__(self, measurement, genie, parent=None):
        super().__init__(parent)

        self._measurement = measurement
        self.genie = genie

        self._sampling_rate = self._measurement.data["data"][0].stats.sampling_rate

        title = "First arrival editor - source: {}, file: {}".format(self._measurement.source_id, self._measurement.file)
        self.setWindowTitle(title)

        grid = QtWidgets.QGridLayout(self)

        # plot axis wiget
        qtg.setConfigOptions(background="w", foreground="k")
        graphic_axis_wiget = qtg.GraphicsLayoutWidget(self)
        plot = graphic_axis_wiget.addPlot(enableMenu=False)
        plot.setLabel('left', "")
        plot.setMouseEnabled(False, False)
        x_max = len(self._measurement.data["data"][0].data) / self._sampling_rate
        plot.setXRange(0, x_max * 1.001, padding=0)
        plot.getAxis('bottom').setStyle(showValues=False)
        plot.getAxis('bottom').hide()
        plot.getAxis('left').setStyle(showValues=False)
        plot.getAxis('left').setHeight(0)
        plot.hideButtons()
        plot.setLabel('top', "Time", units='s')
        plot.getAxis('top').setStyle(showValues=True)
        plot.setLabel('left', " ")
        scroll = QtWidgets.QScrollArea()
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.verticalScrollBar().setVisible(False)
        scroll.setWidgetResizable(True)
        grid.addWidget(scroll, 0, 0, 1, 6)
        sw=QtWidgets.QWidget()
        sw.setMaximumHeight(80)
        scroll.setMaximumHeight(85)
        scroll.setMinimumHeight(85)
        scroll.setWidget(sw)
        hbox = QtWidgets.QHBoxLayout()
        sw.setLayout(hbox)
        label  = QtWidgets.QLabel("Use")
        label.setMinimumWidth(30)
        label.setMaximumWidth(30)
        hbox.addWidget(label)
        hbox.addWidget(graphic_axis_wiget)

        # plot wiget
        self._graphic_wiget = qtg.GraphicsLayoutWidget(self)

        self._plot_list = []
        self._line_list = []
        self._line_auto_list = []
        self._checkbox_list = []

        scroll = QtWidgets.QScrollArea()
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setWidgetResizable(True)
        grid.addWidget(scroll, 1, 0, 3, 6)

        sw=QtWidgets.QWidget()
        scroll.setWidget(sw)

        hbox = QtWidgets.QHBoxLayout()
        sw.setLayout(hbox)

        self._vbox = QtWidgets.QVBoxLayout()
        hbox.addLayout(self._vbox)
        hbox.addWidget(self._graphic_wiget)

        lay = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Auto")
        label.setStyleSheet("QLabel {  color: #00ff00;}")
        lay.addWidget(label)
        label = QtWidgets.QLabel("Manual")
        label.setStyleSheet("QLabel { color : blue; }")
        lay.addWidget(label)
        lay.addStretch()
        grid.addLayout(lay, 6, 0)

        self._close_button = QtWidgets.QPushButton("Close", self)
        self._close_button.clicked.connect(self.reject)
        grid.addWidget(self._close_button, 6, 5)

        self.setLayout(grid)

        self.setMinimumSize(500, 250)
        self.resize(1000, 800)

        self._create_plot()

    def _create_plot(self):
        row = 0
        meas = self._measurement
        data = meas.data["data"]
        for i in range(meas.channel_start - 1, meas.channel_start + abs(meas.receiver_stop - meas.receiver_start)):
            row += 1
            trace = data[i]

            inc = 1 if meas.receiver_stop > meas.receiver_start else -1
            title = "receiver: {}".format(meas.receiver_start + i * inc)
            plot = self._graphic_wiget.addPlot(row=row, col=1, enableMenu=False)
            plot.setLabel('left', title)
            plot.setMouseEnabled(False, False)
            self._plot_list.append(plot)

            checkbox = QtWidgets.QCheckBox()
            checkbox.setMinimumSize(30, 150)
            checkbox.setMaximumWidth(30)
            self._checkbox_list.append(checkbox)
            self._vbox.addWidget(checkbox)

            x_max = len(trace.data) / self._sampling_rate
            x = np.linspace(0, x_max, len(trace.data))
            y = trace.data / np.max(np.abs(trace.data))
            plot.plot(x, y, pen="r")
            plot.setXRange(0, x_max * 1.001, padding=0)
            plot.setYRange(-1, 1, padding=0)
            plot.getAxis('bottom').setStyle(showValues=False)
            plot.getAxis('left').setStyle(showValues=False)
            plot.showGrid(x=True, y=True)
            plot.hideButtons()

            # cross hair auto
            vLineAuto = qtg.InfiniteLine(angle=90, movable=False, pen=qtg.mkPen(qtg.mkColor("g")))
            self._line_auto_list.append(vLineAuto)
            plot.addItem(vLineAuto, ignoreBounds=True)

            # cross hair
            vLine = qtg.InfiniteLine(angle=90, movable=True, pen=qtg.mkPen(qtg.mkColor("b")))
            self._line_list.append(vLine)
            plot.addItem(vLine, ignoreBounds=True)

            fa = self._find_fa(i)
            if fa is not None:
                if fa.verified:
                    t = fa.time
                else:
                    t = -0.1
                vLine.setPos(t)
                checkbox.setChecked(fa.use)
                vLineAuto.setPos(fa.time_auto)

        if self._plot_list:
            self._plot_list[0].scene().sigMouseClicked.connect(self.mouseClickEvent)

        #plot.setLabel('bottom', "Time", units='s')
        #plot.getAxis('bottom').setStyle(showValues=True)

        self._graphic_wiget.setMinimumSize(100, 150 * row)

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            for i, plot in enumerate(self._plot_list):
                if plot.sceneBoundingRect().contains(ev.scenePos()):
                    self._line_list[i].setPos(self._line_auto_list[i].getPos()[0])
                    ev.accept()
                    break

    def _find_fa(self, channel):
        for fa in self.genie.current_inversion_cfg.first_arrivals:
            if fa.file == self._measurement.file and fa.channel == channel:
                return fa
        return None

    def reject(self):
        for i, vLine in enumerate(self._line_list):
            fa = self._find_fa(i)
            if fa is not None:
                line_pos = float(vLine.getPos()[0])
                if line_pos > 0:
                    fa.time = line_pos
                    fa.verified = True
                else:
                    fa.time = 0.0
                    fa.verified = False
                fa.use = self._checkbox_list[i].isChecked()

        super().reject()
