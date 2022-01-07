import os
from genie.core import json_data
from genie.core.xls_parser import XlsLog, XlsLogItem, XlsLogLevel, _empty_cell
import pandas as pd


@json_data.jsondata
class FirstArrival:
    s_x: float = 0.0
    s_y: float = 0.0
    s_z: float = 0.0

    r_x: float = 0.0
    r_y: float = 0.0
    r_z: float = 0.0

    time: float = 0.0

    xls_row: int = 0
    xls_col: int = 0
    has_error: bool = False


def parse_first_arrival(xls_file):
    xls_dir = os.path.dirname(xls_file)

    log = XlsLog()

    with pd.ExcelFile(xls_file) as xls:
        df = pd.read_excel(xls, sheet_name=0, skiprows=0, header=None, dtype=object)

    row_num = df.shape[0]
    col_num = df.shape[1]

    first_arrivals = []

    # read table
    for i in range(5, row_num):
        for j in range(5, col_num):
            if _empty_cell(df[j][i]):
                continue

            first_arrivals.append(FirstArrival(time=df[j][i],
                                               s_x=df[j][0], s_y=df[j][1], s_z=df[j][2],
                                               r_x=df[0][i], r_y=df[1][i], r_z=df[2][i],
                                               xls_row=i, xls_col=j))

    # convert types, check not empty, valid
    for fa in first_arrivals:
        if not (type(fa.time) is float) and not (type(fa.time) is int):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR, fa.xls_row, fa.xls_col,
                                    'Time type must be float or int. Found "{}".'.format(type(fa.time).__name__)))
            fa.has_error = True
        else:
            fa.time = float(fa.time / 1000)

        if _empty_cell(fa.s_x):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR, 0, fa.xls_col, "X is empty."))
            fa.has_error = True
        elif not (type(fa.s_x) is float) and not (type(fa.s_x) is int):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR, 0, fa.xls_col,
                                    'X type must be float or int. Found "{}".'.format(type(fa.s_x).__name__)))
            fa.has_error = True
        else:
            fa.s_x = float(fa.s_x)

        if _empty_cell(fa.s_y):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR, 1, fa.xls_col, "Y is empty."))
            fa.has_error = True
        elif not (type(fa.s_y) is float) and not (type(fa.s_y) is int):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR, 1, fa.xls_col,
                                    'Y type must be float or int. Found "{}".'.format(type(fa.s_y).__name__)))
            fa.has_error = True
        else:
            fa.s_y = float(fa.s_y)

        if _empty_cell(fa.s_z):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR, 2, fa.xls_col, "Z is empty."))
            fa.has_error = True
        elif not (type(fa.s_z) is float) and not (type(fa.s_z) is int):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR, 2, fa.xls_col,
                                    'Z type must be float or int. Found "{}".'.format(type(fa.s_z).__name__)))
            fa.has_error = True
        else:
            fa.s_z = float(fa.s_z)

        if _empty_cell(fa.r_x):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR, fa.xls_row, 0, "X is empty."))
            fa.has_error = True
        elif not (type(fa.r_x) is float) and not (type(fa.r_x) is int):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR,  fa.xls_row, 0,
                                    'X type must be float or int. Found "{}".'.format(type(fa.r_x).__name__)))
            fa.has_error = True
        else:
            fa.r_x = float(fa.r_x)

        if _empty_cell(fa.r_y):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR, fa.xls_row, 1, "Y is empty."))
            fa.has_error = True
        elif not (type(fa.r_y) is float) and not (type(fa.r_y) is int):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR, fa.xls_row, 1,
                                    'Y type must be float or int. Found "{}".'.format(type(fa.r_y).__name__)))
            fa.has_error = True
        else:
            fa.r_y = float(fa.r_y)

        if _empty_cell(fa.r_z):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR, fa.xls_row, 2, "Z is empty."))
            fa.has_error = True
        elif not (type(fa.r_z) is float) and not (type(fa.r_z) is int):
            log.add_item(XlsLogItem(XlsLogLevel.ERROR, fa.xls_row, 2,
                                    'Z type must be float or int. Found "{}".'.format(type(fa.r_z).__name__)))
            fa.has_error = True
        else:
            fa.r_z = float(fa.r_z)

    return first_arrivals, log
