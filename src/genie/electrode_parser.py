from data_types import ElectrodeGroup, Electrode, Measurement

import pandas as pd
import math


# todo: jenom pro testovani
x_fake = 0.0


def parse(file_name):
    ret = {"warnings": [],
           "errors": [],
           "electrode_groups": [],
           "measurements": []}

    with pd.ExcelFile(file_name) as xls:
        if len(xls.sheet_names) < 2:
            ret["errors"].append("ExcelFile must have at least two sheets.")
            return ret
        if xls.sheet_names[0] != "elektrody":
            ret["warnings"].append('Name of first sheet should be "elektrody".')
        if xls.sheet_names[1] != "měření":
            ret["warnings"].append('Name of second sheet should be "měření".')

        #df_e = pd.read_excel(xls, sheet_name=0, usecols="A:H", skiprows=2, header=None, dtype=object)
        #df_e = pd.read_excel(xls, sheet_name=0, usecols="A:E,H:J", skiprows=2, header=None, dtype=object)
        usecols = "A:E,H:J"
        names = ["id", "gallery", "wall", "height", "offset", "x", "y", "z"]
        df_e = pd.read_excel(xls, sheet_name=0, names=names, usecols=usecols, skiprows=2, header=None, dtype=object)

        usecols = "A,I,J,M"
        names = ["electrode", "number", "date", "file"]
        df_m = pd.read_excel(xls, sheet_name=1, names=names, usecols=usecols, skiprows=2, header=None, dtype=object)

    # parse electrodes
    gallery_last = ""
    wall_last = ""
    height_last = ""
    for i in range(df_e.shape[0]):
        # id
        v = df_e["id"][i]
        if type(v) is not int:
            continue
        e_id = v

        # gallery
        v = df_e["gallery"][i]
        if type(v) is str and v != "":
            gallery_last = v

        # wall
        v = df_e["wall"][i]
        if type(v) is str and v != "":
            wall_last = v

        # height
        v = df_e["height"][i]
        if type(v) is str and v != "":
            height_last = v

        eg = _add_electrode_group(ret["electrode_groups"], gallery_last, wall_last, height_last)
        _add_electrode(eg, e_id, df_e["offset"][i], df_e["x"][i], df_e["y"][i], df_e["z"][i])

    # parse measurements
    for i in range(df_m.shape[0]):
        # number
        v = df_m["number"][i]
        if type(v) is not str or v == "":
            continue
        number = v

        # date
        v = df_m["date"][i]
        if type(v) is not pd.Timestamp:
            continue
        date = v.to_pydatetime()

        # file
        v = df_m["file"][i]
        if type(v) is not str or v == "":
            continue
        file = v

        # el start
        v = df_m["electrode"][i]
        if type(v) is not int:
            continue
        el_start = v

        # el stop
        v = df_m["electrode"][i+1]
        if type(v) is not int:
            continue
        el_stop = v

        m = Measurement(number=number, date=date, file=file, el_start=el_start, el_stop=el_stop)
        m.load_data()
        ret["measurements"].append(m)

    return ret


def _add_electrode_group(electrode_groups, gallery, wall, height):
    eg = None
    for item in electrode_groups:
        if item.gallery == gallery and item.wall == wall and item.height == height:
            eg = item
            break
    if eg is None:
        eg = ElectrodeGroup(gallery=gallery, wall=wall, height=height)
        electrode_groups.append(eg)
    return eg


def _add_electrode(group, id, offset, x, y, z):
    # todo: jenom pro testovani
    global x_fake

    def conv(v):
        if type(v) is float:
            if math.isnan(v):
                return None
            else:
                return v
        elif type(v) is int:
            return float(v)
        return None

    offset = conv(offset)
    x = conv(x)
    y = conv(y)
    z = conv(z)

    # if (offset is None) or (x is None) or (y is None) or (z is None):
    #     return

    # todo: jenom pro testovani
    if (offset is None):
        return
    if x is None:
        x = x_fake
        x_fake += 1.0
    if y is None:
        y = 0.0
    if z is None:
        z = 0.0

    group.electrodes.append(Electrode(id=id, offset=offset, x=x, y=y, z=z))
