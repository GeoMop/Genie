from PyQt5 import QtWidgets, QtGui


class Measurements_model(QtWidgets.QMainWindow):
    def __init__(self, meas_model_file):
        super().__init__()

        self.meas_model_file = meas_model_file

        # edit for output
        self._output_edit = QtWidgets.QTextEdit()
        self._output_edit.setReadOnly(True)
        font = QtGui.QFont("monospace")
        font.setStyleHint(QtGui.QFont.TypeWriter)
        self._output_edit.setFont(font)

        self.setCentralWidget(self._output_edit)

        self._show()

    def _show(self):
        log = ""
        self._output_edit.clear()

        with open(self.meas_model_file) as fd:
            log += fd.read()

        self._output_edit.moveCursor(QtGui.QTextCursor.End)
        self._output_edit.insertPlainText(log)
        self._output_edit.moveCursor(QtGui.QTextCursor.Start)
