from PyQt5 import QtWidgets, QtGui, QtCore

import sys
import os
import threading
import math
import time
import subprocess
import random


class BadFormatError(Exception):
    """Raised when error in point cloud format."""
    pass


class PointCloudReaderDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, enable_import=False, work_dir=""):
        super().__init__(parent)
        self._log_text = ""
        self._enable_import = enable_import
        self._import_ready = False
        self._work_dir = work_dir

        self._out_file = os.path.join(self._work_dir, "point_cloud.tmp.xyz")
        self._out_file_red = os.path.join(self._work_dir, "point_cloud_red.tmp.xyz")
        #self._point_cloud_pixmap_file = os.path.join(self._work_dir, "point_cloud_pixmap.png.tmp")
        self._meshlab_script = os.path.join(self._work_dir, "meshlab_merge.mlx")

        self.origin_x = 0.0
        self.origin_y = 0.0
        self.origin_z = 0.0

        self.pixmap_x_min = 0.0
        self.pixmap_y_min = 0.0
        self.pixmap_scale = 1.0

        self._thread = None
        self._stop_thread = False
        self._message_queue = []
        self._point_cloud_file = ""
        self._pixmap_mat = []
        self._timer = QtCore.QTimer()
        self._closing = False
        self._meshlab_proc = None

        self.setWindowTitle("Open point cloud file")

        main_layout = QtWidgets.QVBoxLayout()

        file_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Point cloud file:")
        file_layout.addWidget(label)
        self._file_edit = QtWidgets.QLineEdit()
        #self._file_edit.returnPressed.connect(self._handle_read_action)
        file_layout.addWidget(self._file_edit)
        self._browse_button = QtWidgets.QPushButton("Browse...")
        self._browse_button.clicked.connect(self._handle_browse_action)
        file_layout.addWidget(self._browse_button)
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

        merge_layout = QtWidgets.QHBoxLayout()
        merge_layout.addWidget(QtWidgets.QLabel("Merge close points:"))
        self._merge_checkbox = QtWidgets.QCheckBox()
        self._merge_checkbox.setToolTip("If checked close points are merged together.")
        merge_layout.addWidget(self._merge_checkbox)
        merge_layout.addWidget(QtWidgets.QLabel("Distance:"))
        self._merge_distance_edit = QtWidgets.QLineEdit()
        self._merge_distance_edit.setEnabled(False)
        self._merge_distance_edit.setValidator(QtGui.QDoubleValidator())
        self._merge_distance_edit.setText("0.1")
        self._merge_distance_edit.setToolTip("All the points that closer than this threshold are merged together. [m]")
        merge_layout.addWidget(self._merge_distance_edit)
        main_layout.addLayout(merge_layout)

        self._merge_checkbox.stateChanged.connect(self._handle_merge_distance_checkbox_changed)

        # button box
        self._read_button = QtWidgets.QPushButton("Read")
        self._read_button.clicked.connect(self._handle_read_action)
        self._save_results_button = QtWidgets.QPushButton("Save results...")
        self._save_results_button.clicked.connect(self._handle_save_results_action)
        self._import_button = QtWidgets.QPushButton("Import")
        self._import_button.clicked.connect(self._handle_import_action)
        self._import_button.setEnabled(False)
        button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        button_box.addButton(self._read_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(self._save_results_button, QtWidgets.QDialogButtonBox.ActionRole)
        button_box.addButton(self._import_button, QtWidgets.QDialogButtonBox.ActionRole)
        self._close_button = button_box.button(QtWidgets.QDialogButtonBox.Close)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)

        self.resize(600, 300)

    def _handle_merge_distance_checkbox_changed(self, state=None):
        self._merge_distance_edit.setEnabled(self._merge_checkbox.isChecked())

    def _enable_ctrl(self, enable=True):
        self._file_edit.blockSignals(not enable)
        self._browse_button.setEnabled(enable)
        self._save_results_button.setEnabled(enable)
        self._import_button.setEnabled(enable and self._import_ready and self._enable_import)
        self._merge_checkbox.setEnabled(enable)
        self._merge_distance_edit.setEnabled(enable and self._merge_checkbox.isChecked())

    def _pre_thread(self):
        self._enable_ctrl(False)

        self._log.clear()
        self._pixmap_mat = []
        self._stop_thread = False

        self._thread = threading.Thread(target=self._thread_run, daemon=True)
        self._thread.start()

        self._read_button.setText("Stop")

        self._timer.timeout.connect(self._handle_timeout)
        self._timer.start(100)

    def _copy_cloud(self, src, dst):
        points_count = 0
        points_count_show = 1000000
        points_count_test_stop = 10000

        with open(src) as fd_in:
            with open(dst, "w") as fd_out:
                for line in fd_in:
                    s = line.split()
                    if len(s) >= 3:
                        fd_out.write("{} {} {}\n".format(*s[:3]))
                        points_count += 1
                        if points_count % points_count_show == 0:
                            self._message_queue.append("{} points copied.".format(points_count))
                        if points_count % points_count_test_stop == 0:
                            if self._stop_thread:
                                return
                self._message_queue.append("{} points copied.".format(points_count))

    def _reduce_cloud(self, src, dst, red_count=5000):
        points_count = 0
        points_count_show = 1000000
        points_count_test_stop = 10000

        out = []
        with open(src) as fd_in:
            line = ""
            for i in range(red_count):
                line = fd_in.readline()
                if line:
                    out.append(line)
                    points_count += 1
                else:
                    break
            p = 1
            while line:
                p += 1
                t = 1.0 / p
                for i in range(red_count):
                    line = fd_in.readline()
                    if line:
                        if random.random() < t:
                            out[i] = line
                        points_count += 1
                        if points_count % points_count_show == 0:
                            self._message_queue.append("{} points reduced.".format(points_count))
                        if points_count % points_count_test_stop == 0:
                            if self._stop_thread:
                                return
                    else:
                        break
            self._message_queue.append("{} points reduced.".format(points_count))

        with open(dst, "w") as fd_out:
            fd_out.writelines(out)

    def _thread_run(self):
        self._import_ready = False

        # copy points
        self._message_queue.append("Copying points")
        t = time.time()
        self._copy_cloud(self._point_cloud_file, self._out_file)

        if self._stop_thread:
            self._message_queue.append("\nCopying points stopped.")
            self._message_queue.append(None)
            return

        self._message_queue.append("Copying points done in {:0.3f} s.".format(time.time() - t))

        # meshlab
        if self._merge_checkbox.isChecked():
            self._message_queue.append("\nMerging points")
            t = time.time()
            merge_script_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "merge.py")
            args = [sys.executable, merge_script_path, self._out_file, self._merge_distance_edit.text()]
            self._meshlab_proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            for line in self._meshlab_proc.stdout:
                if line and line[-1] == "\n":
                    line = line[:-1]
                self._message_queue.append(line)
            self._meshlab_proc.wait()
            self._meshlab_proc = None

            if self._stop_thread:
                self._message_queue.append("\nMerging points stopped.")
                self._message_queue.append(None)
                return

            self._message_queue.append("Merging points done in {:0.3f} s.".format(time.time() - t))

        # reduce points
        self._message_queue.append("\nReducing points")
        t = time.time()
        self._reduce_cloud(self._out_file, self._out_file_red)

        if self._stop_thread:
            self._message_queue.append("\nReducing points stopped.")
            self._message_queue.append(None)
            return

        self._message_queue.append("Reducing points done in {:0.3f} s.".format(time.time() - t))

        self._message_queue.append(None)
        self._import_ready = True

    def _thread_run_old(self):
        def xy_gen(fd):
            try:
                line = fd.readline()
                while line:
                    s = line.split()
                    if len(s) >= 3:
                        try:
                            x = float(s[0])
                            y = float(s[1])
                        except ValueError:
                            raise BadFormatError
                        else:
                            out_line = s[0] + " " + s[1] + " " + s[2]
                            yield x, y, out_line
                    line = fd.readline()
            except UnicodeDecodeError:
                raise BadFormatError

        try:
            t = time.time()
            points_count_show = 1000000
            points_count_test_stop = 10000
            with open(self._point_cloud_file) as fd:
                # determine range
                self._message_queue.append("Phase 1")

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
                        self._message_queue.append("{} points read.".format(points_count))
                    if points_count % points_count_test_stop == 0:
                        if self._stop_thread:
                            self._message_queue.append("\nReading stopped.")
                            self._message_queue.append(None)
                            return

                self._message_queue.append("{} points read.".format(points_count))

                # create pixmap, save output file
                self._message_queue.append("\nPhase 2")

                x_max_min = x_max - x_min
                y_max_min = y_max - y_min
                max_min = max(x_max_min, y_max_min)
                pixmap_size = math.ceil(math.sqrt(points_count))
                if pixmap_size < 100:
                    pixmap_size = 100
                elif pixmap_size > 1000:
                    pixmap_size = 1000
                max_min_pixmap_size = max_min / pixmap_size
                pixmap_size_x = math.floor(x_max_min / max_min_pixmap_size)
                pixmap_size_y = math.floor(y_max_min / max_min_pixmap_size)
                self._pixmap_mat = [[False] * pixmap_size_x for _ in range(pixmap_size_y)]
                with open(self._out_file, "w") as fd_out:
                    fd.seek(0)
                    points_count = 0
                    for x, y, out_line in xy_gen(fd):
                        i = math.floor((x - x_min) / max_min_pixmap_size)
                        j = math.floor((y - y_min) / max_min_pixmap_size)
                        if i >= pixmap_size_x:
                            i = pixmap_size_x - 1
                        if j >= pixmap_size_y:
                            j = pixmap_size_y - 1
                        self._pixmap_mat[j][i] = True
                        fd_out.write(out_line + "\n")
                        points_count += 1
                        if points_count % points_count_show == 0:
                            self._message_queue.append("{} points read.".format(points_count))
                        if points_count % points_count_test_stop == 0:
                            if self._stop_thread:
                                self._message_queue.append("\nReading stopped.")
                                self._message_queue.append(None)
                                return
                    self._message_queue.append("{} points read.".format(points_count))
            self._message_queue.append("\nPoints reading done in {:0.3f} s.".format(time.time() - t))
            self.pixmap_x_min = x_min
            self.pixmap_y_min = y_min
            self.pixmap_scale = max_min_pixmap_size
        except BadFormatError:
            self._message_queue.append("\nBad point cloud file format.")
        self._message_queue.append(None)

    def _post_thread(self):
        self._thread.join()
        self._thread = None

        # if self._pixmap_mat:
        #     # create pixmap
        #     pixmap = QtGui.QPixmap(len(self._pixmap_mat[0]), len(self._pixmap_mat))
        #     pixmap.fill(QtCore.Qt.transparent)
        #     painter = QtGui.QPainter(pixmap)
        #     pen = QtGui.QPen(QtGui.QColor("black"))
        #     painter.setPen(pen)
        #     for j, line in enumerate(self._pixmap_mat):
        #         for i, b in enumerate(line):
        #             if b:
        #                 painter.drawPoint(i, j)
        #     painter.end()
        #
        #     # save pixmap
        #     tr_pixmap = pixmap.transformed(QtGui.QTransform.fromScale(1, -1))
        #     tr_pixmap.save(self._point_cloud_pixmap_file, "PNG")
        #
        #     self._import_ready = True
        # else:
        #     self._import_ready = False

        self._log_text = self._log.toPlainText()

        self._enable_ctrl(True)

        self._read_button.setText("Read")

        self._timer.stop()

        if self._closing:
            self._clean_up()
            super().reject()

    def _handle_read_action(self):
        if self._thread is None:
            self._point_cloud_file = self._file_edit.text()
            if not os.path.isfile(self._point_cloud_file):
                return

            self._pre_thread()
        else:
            self._stop_thread = True
            if self._meshlab_proc is not None:
                self._meshlab_proc.kill()

    def _handle_save_results_action(self):
        if self._log_text:
            file = QtWidgets.QFileDialog.getSaveFileName(self, "Save results to file",
                                                         os.path.join(self._work_dir, "results.txt"),
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
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Open point cloud file", "", "Point Cloud Files (*)")[0]
        if file:
            self._file_edit.setText(file)

            app = QtWidgets.QApplication.instance()
            app.processEvents(QtCore.QEventLoop.AllEvents, 0)

            #self._handle_read_action()

    def _handle_timeout(self):
        if self._thread is not None:
            l = len(self._message_queue)
            for i in range(l):
                text = self._message_queue.pop(0)
                if text is None:
                    self._post_thread()
                    return
                else:
                    self._log.append(text)
                    self._log.moveCursor(QtGui.QTextCursor.End)

            if not self._thread.is_alive():
                self._post_thread()

    def reject(self):
        if self._thread is not None:
            self._stop_thread = True
            self._closing = True
            return
        else:
            self._clean_up()
            super().reject()

    def _clean_up(self):
        # remove tmp files
        if os.path.exists(self._out_file):
            os.remove(self._out_file)
        if os.path.exists(self._out_file_red):
            os.remove(self._out_file_red)

    def keyPressEvent(self, evt):
        if evt.key() == QtCore.Qt.Key_Enter or evt.key() == QtCore.Qt.Key_Return:
            return
        super().keyPressEvent(evt)


if __name__ == '__main__':
    def main():
        app = QtWidgets.QApplication(sys.argv)
        dialog = PointCloudReaderDialog()
        dialog.show()
        sys.exit(app.exec())

    main()
