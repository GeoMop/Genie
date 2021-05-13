from PyQt5 import QtWidgets, QtCore, QtGui

from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

import os


class MisfitLog(QtWidgets.QWidget):
    def __init__(self, main_window, parent=None):
        super().__init__(parent)

        self.genie = main_window.genie

        self.misfit_log = []

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        self.canvas = FigureCanvas(Figure())
        self.canvas.figure.subplots_adjust(left=0.1, right=0.9, top=0.95, bottom=0.1)
        layout.addWidget(self.canvas)

        self._static_ax = self.canvas.figure.subplots()
        self._static_ax_lam = self._static_ax.twinx()

        self.update_log()

    def update_log(self):
        if self.genie.project_cfg is not None:
            file_name = os.path.join(self.genie.cfg.current_project_dir, "inversions",
                                     self.genie.project_cfg.curren_inversion_name, "inv_log.txt")
            if os.path.isfile(file_name):
                self.misfit_log = self.parse(file_name)

        self.show_log()

    def parse(self, file_name):
        misfit_log = []

        with open(file_name) as fd:
            lines = fd.readlines()

        last_iter = -1
        try:
            for l in lines:
                i = l.find("Phi =")
                if i >= 0:
                    s = l.split(":", 1)
                    iter = int(s[0])

                    s = l.split("=")
                    x = s[1]

                    s = x.split("*")
                    lam = float(s[-1])

                    x = s[0]
                    i = x.find("+")
                    if x[i - 1] == "e":
                        i = x.find("+", i + 1)

                    misfit = float(x[:i])
                    reg = float(x[i + 1:]) * lam

                    t = (misfit, reg, lam)
                    if iter == last_iter:
                        misfit_log[-1] = t
                    else:
                        misfit_log.append(t)

                    last_iter = iter
        except Exception:
            pass

        return misfit_log

    def show_log(self):
        self._static_ax.cla()
        self._static_ax.set_yscale('log')
        self._static_ax.set_xlabel('Iteration')
        self._static_ax.set_ylabel('Misfit, Regularization')

        self._static_ax_lam.cla()
        self._static_ax_lam.set_ylabel('Lambda')

        self._static_ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

        if self.misfit_log:
            self._static_ax.plot([item[0] for item in self.misfit_log], color="tab:blue", label="Misfit")
            self._static_ax.plot([item[1] for item in self.misfit_log], color="tab:orange", label="Regularization")
            self._static_ax_lam.plot([item[2] for item in self.misfit_log], color="tab:green")

            self._static_ax.plot([], color="tab:green", label="Lambda")
            self._static_ax.legend()

        self.canvas.draw_idle()
