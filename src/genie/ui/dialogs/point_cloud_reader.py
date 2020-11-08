from PyQt5 import QtWidgets, QtGui, QtCore

import sys
import os


class PointCloudReaderDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, enable_import=False, work_dir=""):
        super().__init__(parent)
        self._log_text = ""
        self._enable_import = enable_import
        self._work_dir = work_dir

        self._out_file = os.path.join(self._work_dir, "point_cloud.xyz.tmp")
        self._point_cloud_pixmap_file = os.path.join(self._work_dir, "point_cloud_pixmap.png.tmp")

        self.origin_x = 0.0
        self.origin_y = 0.0
        self.origin_z = 0.0

        self.pixmap_x_min = 0.0
        self.pixmap_y_min = 0.0
        self.pixmap_scale = 1.0

        self.setWindowTitle("PointCloudReader")

        main_layout = QtWidgets.QVBoxLayout()

        file_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Point cloud file:")
        file_layout.addWidget(label)
        self._file_edit = QtWidgets.QLineEdit()
        file_layout.addWidget(self._file_edit)
        browse_button = QtWidgets.QPushButton("Browse...")
        browse_button.clicked.connect(self._handle_browse_action)
        file_layout.addWidget(browse_button)
        main_layout.addLayout(file_layout)

        self._log = QtWidgets.QTextEdit(self)
        self._log.setReadOnly(True)
        self._log.setFont(QtGui.QFont("monospace"))
        main_layout.addWidget(self._log)

        origin_layout = QtWidgets.QHBoxLayout()
        origin_layout.addWidget(QtWidgets.QLabel("Point cloud origin:"))
        origin_layout.addWidget(QtWidgets.QLabel("x:"))
        self._origin_x_edit = QtWidgets.QLineEdit()
        self._origin_x_edit.setValidator(QtGui.QDoubleValidator())
        self._origin_x_edit.setText("-622000.0")
        origin_layout.addWidget(self._origin_x_edit)
        origin_layout.addWidget(QtWidgets.QLabel("y:"))
        self._origin_y_edit = QtWidgets.QLineEdit()
        self._origin_y_edit.setValidator(QtGui.QDoubleValidator())
        self._origin_y_edit.setText("-1128000.0")
        origin_layout.addWidget(self._origin_y_edit)
        origin_layout.addWidget(QtWidgets.QLabel("z:"))
        self._origin_z_edit = QtWidgets.QLineEdit()
        self._origin_z_edit.setValidator(QtGui.QDoubleValidator())
        self._origin_z_edit.setText("0.0")
        origin_layout.addWidget(self._origin_z_edit)
        main_layout.addLayout(origin_layout)

        # button box
        read_button = QtWidgets.QPushButton("Read")
        read_button.clicked.connect(self._handle_read_action)
        save_results_button = QtWidgets.QPushButton("Save results...")
        save_results_button.clicked.connect(self._handle_save_results_action)
        self._import_button = QtWidgets.QPushButton("Import")
        self._import_button.clicked.connect(self._handle_import_action)
        self._import_button.setEnabled(False)
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        button_box.addButton(read_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(save_results_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(self._import_button, QtWidgets.QDialogButtonBox.ActionRole)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

        self.resize(600, 300)

    def _handle_read_action(self):
        point_cloud_file = self._file_edit.text()
        if not os.path.isfile(point_cloud_file):
            return

        self._log.clear()

        def xy_gen(fd):
            line = fd.readline()
            while line:
                s = line.split()
                if len(s) >= 3:
                    x = float(s[0])
                    y = float(s[1])
                    out_line = s[0] + " " + s[1] + " " + s[2]
                    yield x, y, out_line
                line = fd.readline()

        points_count_show = 1000000
        with open(point_cloud_file) as fd:
            # determine range
            self._log.append("Phase 1")
            self._log.moveCursor(QtGui.QTextCursor.End)
            self._log.repaint()

            gen = xy_gen(fd)
            x, y, _ = next(gen)
            points_count = 1
            x_min = x_max = x
            y_min = y_max = y
            for x, y, _ in gen:
                if x < x_min:
                    x_min = x
                elif x > x_max:
                    x_max = x
                if y < y_min:
                    y_min = y
                elif y > y_max:
                    y_max = y
                points_count += 1
                if points_count % points_count_show == 0:
                    self._log.append("{} points read.".format(points_count))
                    self._log.moveCursor(QtGui.QTextCursor.End)
                    self._log.repaint()

            self._log.append("{} points read.".format(points_count))
            self._log.moveCursor(QtGui.QTextCursor.End)
            self._log.repaint()

            # create pixmap, save output file
            self._log.append("\nPhase 2")
            self._log.moveCursor(QtGui.QTextCursor.End)
            self._log.repaint()

            x_max_min = x_max - x_min
            y_max_min = y_max - y_min
            max_min = max(x_max_min, y_max_min)
            pixmap_size = 1000
            max_min_pixmap_size = max_min / pixmap_size
            pixmap = QtGui.QPixmap(x_max_min / max_min_pixmap_size, y_max_min / max_min_pixmap_size)
            pixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(pixmap)
            pen = QtGui.QPen(QtGui.QColor("black"))
            painter.setPen(pen)
            with open(self._out_file, "w") as fd_out:
                fd.seek(0)
                points_count = 0
                for x, y, out_line in xy_gen(fd):
                    painter.drawPoint((x - x_min) / max_min_pixmap_size, (y - y_min) / max_min_pixmap_size)
                    fd_out.write(out_line + "\n")
                    points_count += 1
                    if points_count % points_count_show == 0:
                        self._log.append("{} points read.".format(points_count))
                        self._log.moveCursor(QtGui.QTextCursor.End)
                        self._log.repaint()
            painter.end()

            self._log.append("{} points read.".format(points_count))
            self._log.moveCursor(QtGui.QTextCursor.End)
            self._log.repaint()

        # save pixmap
        tr_pixmap = pixmap.transformed(QtGui.QTransform.fromScale(1, -1))
        tr_pixmap.save(self._point_cloud_pixmap_file, "PNG")
        self.pixmap_x_min = x_min
        self.pixmap_y_min = y_min
        self.pixmap_scale = max_min_pixmap_size

        self._log.append("\nPoints reading done.")
        self._log.moveCursor(QtGui.QTextCursor.End)

        self._log_text = self._log.toPlainText()

        if self._enable_import:
            self._import_button.setEnabled(True)

    def _handle_save_results_action(self):
        if self._log_text:
            file = QtWidgets.QFileDialog.getSaveFileName(self, "Save results to file",
                                                         os.path.join(self.directory, "results.txt"),
                                                         "Text Files (*.txt)")
            file_name = file[0]
            if file_name:
                with open(file_name, 'w') as fd:
                    fd.write(self._log_text)

    def _handle_import_action(self):
        self.origin_x = float(self._origin_x_edit.text())
        self.origin_y = float(self._origin_y_edit.text())
        self.origin_z = float(self._origin_z_edit.text())

        self.accept()

    def _handle_browse_action(self):
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Open point cloud file", "", "Point Cloud Files (*)")
        self._file_edit.setText(file[0])

    def reject(self):
        # remove tmp files
        if os.path.exists(self._out_file):
            os.remove(self._out_file)
        if os.path.exists(self._point_cloud_pixmap_file):
            os.remove(self._point_cloud_pixmap_file)

        super().reject()


if __name__ == '__main__':
    def main():
        app = QtWidgets.QApplication(sys.argv)
        dialog = PointCloudReaderDialog()
        dialog.show()
        sys.exit(app.exec())

    main()
