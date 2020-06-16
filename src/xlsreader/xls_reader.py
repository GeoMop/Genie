import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from xlsreader.xls_reader_dialog import XlsReaderDialog

from PyQt5 import QtWidgets, QtGui


if __name__ == '__main__':
    def main():
        app = QtWidgets.QApplication(sys.argv)
        dialog = XlsReaderDialog()
        dialog.show()
        sys.exit(app.exec())

    main()
