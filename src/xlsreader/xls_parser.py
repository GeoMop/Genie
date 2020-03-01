from xlsreader import ares_parser

import os
import sys
import re
from enum import Enum
from typing import List
import attr
import math
import json
import json_data
import pandas as pd


@json_data.jsondata
class XlsElectrode:
    id: int = 0
    gallery: str = ""
    wall: str = ""
    height: str = ""
    meas_id: int = 0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    xls_row: int = 0


@json_data.jsondata
class XlsMeasurement:
    number: str = ""
    """Measurement number, this is key"""
    date: str = ""
    file: str = ""
    xls_row: int = 0


@json_data.jsondata
class XlsMeasurementGroup:
    electrodes: List[XlsElectrode] = attr.ib(factory=list)
    measurements: List[XlsMeasurement] = attr.ib(factory=list)
    xls_row: int = 0


class XlsLogLevel(Enum):
    INFO = 1
    WARNING = 2
    ERROR = 3


class XlsLogItem:
    def __init__(self, level=XlsLogLevel.INFO, xls_row=0, text=""):
        self.level = level
        self.xls_row = xls_row
        self.text = text

class XlsLog:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def to_string(self):
        items = sorted(self.items, key=lambda x: x.xls_row)
        texts = ["{} row: {}, {}".format(item.level.name, item.xls_row, item.text) for item in items]
        return "\n".join(texts)


def _empty_cell(v):
    return (type(v) is float) and math.isnan(v)


_white_space_pattern = re.compile(r"\s")
def _white_space_diacritics(v):
    if _white_space_pattern.search(v) is not None:
        return True
    for c in v:
        if ord(c) > 127:
            return True
    return False


def _get_el_set_file(file):
    res = ares_parser.parse(file)
    data = res["data"]
    s = set()
    s.update(data["ca"])
    s.update(data["cb"])
    s.update(data["pa"])
    s.update(data["pb"])
    return s


def parse(xls_file):
    xls_dir = os.path.dirname(xls_file)

    log = XlsLog()

    with pd.ExcelFile(xls_file) as xls:
        df = pd.read_excel(xls, sheet_name=0, skiprows=0, header=None, dtype=object)

    df[1] = df[1].fillna(method='ffill')
    df[2] = df[2].fillna(method='ffill')
    df[3] = df[3].fillna(method='ffill')

    row_num = df.shape[0]
    col_num = df.shape[1]

    measurements_groups = []

    # read table
    mg = None
    for i in range(2, row_num):
        xls_row = i + 1

        if type(df[0][i]) is not int:
            if mg is not None:
                measurements_groups.append(mg)
                mg = None
            continue

        if mg is None:
            mg = XlsMeasurementGroup(xls_row=xls_row)

            for j in range(10, col_num, 10):
                if j + 10 > col_num:
                    break
                if _empty_cell(df[j][i]):
                    continue
                number = str(df[j][i]).strip()
                if number:
                    mg.measurements.append(XlsMeasurement(number=number, date=df[j + 1][i], file=df[j + 4][i],
                                                          xls_row=xls_row))
        mg.electrodes.append(XlsElectrode(id=df[0][i], gallery=df[1][i], wall=df[2][i], height=df[3][i],
                                          meas_id=df[5][i], x=df[7][i], y=df[8][i], z=df[9][i], xls_row=xls_row))
    if mg is not None:
        measurements_groups.append(mg)

    # with open("raw_out.txt", "w") as fd:
    #     fd.write(df.to_string())

    # convert types, check not empty, valid
    for mg in measurements_groups:
        for e in mg.electrodes:
            if _empty_cell(e.gallery):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "Gallery is empty."))
                e.gallery = ""
            else:
                e.gallery = str(e.gallery).strip()

            if _empty_cell(e.wall):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "Wall is empty."))
                e.wall = ""
            else:
                e.wall = str(e.wall).strip()

            if _empty_cell(e.height):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "Height is empty."))
                e.height = ""
            else:
                e.height = str(e.height).strip()

            if _empty_cell(e.meas_id):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "Electrode measurement id is empty."))
                e.meas_id = ""
            else:
                e.meas_id = str(e.meas_id).strip()

            if _empty_cell(e.x):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "X is empty."))
            elif not (type(e.x) is float) and not (type(e.x) is int):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "X type must be float or int."))
            else:
                e.x = float(e.x)

            if _empty_cell(e.y):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "Y is empty."))
            elif not (type(e.y) is float) and not (type(e.y) is int):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "Y type must be float or int."))
            else:
                e.y = float(e.y)

            if _empty_cell(e.z):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "Z is empty."))
            elif not (type(e.z) is float) and not (type(e.z) is int):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "Z type must be float or int."))
            else:
                e.z = float(e.z)

        for m in mg.measurements:
            if _white_space_diacritics(m.number):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, m.xls_row, "Measurement number must not contain white space nor diacritics."))

            if _empty_cell(m.date):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, m.xls_row, "Date is empty."))
                m.date = ""
            else:
                m.date = str(m.date).strip()
                if not m.date:
                    log.add_item(XlsLogItem(XlsLogLevel.ERROR, m.xls_row, "Date is empty."))

            if _empty_cell(m.file):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, m.xls_row, "File is empty."))
                m.file = ""
            else:
                m.file = str(m.file).strip()
                if not m.file:
                    log.add_item(XlsLogItem(XlsLogLevel.ERROR, m.xls_row, "File is empty."))
                elif _white_space_diacritics(m.file):
                    log.add_item(XlsLogItem(XlsLogLevel.ERROR, m.xls_row, "File must not contain white space nor diacritics."))

    # check that duplicate electrode are the same
    ed = {}
    for mg in measurements_groups:
        for e in mg.electrodes:
            if e.id in ed:
                e_ed = ed[e.id]
                if e.x != e_ed.x:
                    log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "X is different from same electrode on row {}.".format(e_ed.xls_row)))
                if e.y != e_ed.y:
                    log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "Y is different from same electrode on row {}.".format(e_ed.xls_row)))
                if e.z != e_ed.z:
                    log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "X is different from same electrode on row {}.".format(e_ed.xls_row)))
                if e.gallery != e_ed.gallery:
                    log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "Gallery is different from same electrode on row {}.".format(e_ed.xls_row)))
                if e.wall != e_ed.wall:
                    log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "Wall is different from same electrode on row {}.".format(e_ed.xls_row)))
                if e.height != e_ed.height:
                    log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, "Height is different from same electrode on row {}.".format(e_ed.xls_row)))
            else:
                ed[e.id] = e

    # measurement files exist and have same elecrodes
    for mg in measurements_groups:
        for m in mg.measurements:
            if not m.file:
                continue
            f = os.path.join(xls_dir, m.number, m.file)
            if not os.path.isfile(f):
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, 'File "{}" not exist'.format(f)))
            else:
                m_file_el_set = _get_el_set_file(f)
                m_el_set = {e.meas_id for e in mg.electrodes}
                log.add_item(XlsLogItem(XlsLogLevel.WARNING, e.xls_row, 'Measurement "{}" has {} electrode ids which are not in measurement file'.format(m.number, m_el_set - m_file_el_set)))
                log.add_item(XlsLogItem(XlsLogLevel.ERROR, e.xls_row, 'Measurement "{}" has {} electrode ids which are not in xls file.'.format(m.number, m_file_el_set - m_el_set)))

    # with open("out.json", "w") as fd:
    #     json.dump([mg.serialize() for mg in measurements_groups], fd, indent=4, sort_keys=True)

    return measurements_groups, log


if __name__ == '__main__':
    measurements_groups, log = parse(sys.argv[1])
    print(log.to_string())
