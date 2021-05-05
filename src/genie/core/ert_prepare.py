import pandas as pd
#import pybert as pb
import pygimli as pg
import numpy as np

from .data_types import MeasurementInfoItem, MeasurementsInfo
from genie.core import cut_point_cloud


def prepare_old(electrode_groups, measurements):
    """
    Prepares data for GIMLI inversion.
    :param electrode_groups:
    :param measurements:
    :return:
    """
    el_offset = 0
    electrodes = []
    a = pd.Series()
    b = pd.Series()
    m = pd.Series()
    n = pd.Series()
    i = pd.Series()
    u = pd.Series()
    err = pd.Series()
    rhoa = pd.Series()

    for ms in measurements:
        if ms.data is None:
            continue
        d = ms.data["data"]

        for e_id in range(ms.el_start, ms.el_stop+1):
            e = _find_el(electrode_groups, e_id)
            if e is None:
                print("chyba")
            electrodes.append(e)

        a = a.append(d["ca"] + el_offset, ignore_index=True)
        b = b.append(d["cb"] + el_offset, ignore_index=True)
        m = m.append(d["pa"] + el_offset, ignore_index=True)
        n = n.append(d["pb"] + el_offset, ignore_index=True)
        i = i.append(d["I"], ignore_index=True)
        u = u.append(d["V"], ignore_index=True)
        err = err.append(d["std"], ignore_index=True)
        rhoa = rhoa.append(d["AppRes"], ignore_index=True)

        el_offset += ms.el_stop - ms.el_start + 1

    data = pg.DataContainerERT()
    for e in electrodes:
        data.createSensor([e.x, e.y, e.z])
    data.resize(len(a))
    data.set('a', a)
    data.set('b', b)
    data.set('m', m)
    data.set('n', n)
    data.set('i', i)
    data.set('u', u)
    data.set('err', err)
    data.set('rhoa', rhoa)
    data.markValid(data('rhoa') > 0)
    return data


def prepare_old2(electrode_groups, measurements):
    """
    Prepares data for GIMLI inversion.
    :param electrode_groups:
    :param measurements:
    :return:
    """
    #el_offset = 0
    electrodes = []
    a = pd.Series()
    b = pd.Series()
    m = pd.Series()
    n = pd.Series()
    i = pd.Series()
    u = pd.Series()
    err = pd.Series()
    rhoa = pd.Series()

    for ms in measurements:
        if ms.data is None:
            continue
        d = ms.data["data"]

        meas_map_sensor = {}
        for meas_id, e_id in ms.meas_map.items():
            ind = -1
            for j, e in enumerate(electrodes):
                if e.id == e_id:
                    ind = j
                    break
            if ind < 0:
                e = _find_el(electrode_groups, e_id)
                if e is None:
                    print("chyba")
                ind = len(electrodes)
                electrodes.append(e)
            meas_map_sensor[meas_id] = ind

        a = a.append(pd.Series([meas_map_sensor[v] for v in d["ca"]]), ignore_index=True)
        b = b.append(pd.Series([meas_map_sensor[v] for v in d["cb"]]), ignore_index=True)
        m = m.append(pd.Series([meas_map_sensor[v] for v in d["pa"]]), ignore_index=True)
        n = n.append(pd.Series([meas_map_sensor[v] for v in d["pb"]]), ignore_index=True)
        i = i.append(d["I"], ignore_index=True)
        u = u.append(d["V"], ignore_index=True)
        err = err.append(d["std"], ignore_index=True)
        rhoa = rhoa.append(d["AppRes"], ignore_index=True)

        #el_offset += len(ms.meas_map)

    data = pg.DataContainerERT()
    for e in electrodes:
        data.createSensor([e.x, e.y, e.z])
    data.resize(len(a))
    data.set('a', a)
    data.set('b', b)
    data.set('m', m)
    data.set('n', n)
    data.set('i', i)
    data.set('u', u)
    data.set('err', err)
    data.set('rhoa', rhoa)
    data.markValid(data('rhoa') > 0)
    return data


def prepare(electrode_groups, measurements, mesh_cut_tool_param=None, masked_meas_lines=None):
    """
    Prepares data for GIMLI inversion.
    :param electrode_groups:
    :param measurements:
    :return:
    """
    #el_offset = 0
    electrodes = []
    sensor_ids = []
    a = pd.Series()
    b = pd.Series()
    m = pd.Series()
    n = pd.Series()
    i = pd.Series()
    u = pd.Series()
    err = pd.Series()
    rhoa = pd.Series()

    meas_info = MeasurementsInfo()

    data = pg.DataContainerERT()

    if mesh_cut_tool_param is not None:
        base_point, gen_vecs = cut_point_cloud.cut_tool_to_gen_vecs(mesh_cut_tool_param, only_inv=True)
        inv_tr_mat = cut_point_cloud.inv_tr(gen_vecs)

    for ms in measurements:
        if ms.data is None:
            continue
        d = ms.data["data"]

        ind_to_rem = set()

        # remove masked lines from measurements
        if masked_meas_lines is not None:
            if ms.number in masked_meas_lines:
                ind_to_rem.update({i for i, b in enumerate(masked_meas_lines[ms.number][:d.shape[0]]) if b})

        # remove measurements outside inversion region
        if mesh_cut_tool_param is not None:
            for j in range(d.shape[0]):
                for col in ["ca", "cb", "pa", "pb"]:
                    e = _find_el(electrode_groups, ms.meas_map[d[col][j]])
                    nl = cut_point_cloud.tr_to_local(base_point, inv_tr_mat, np.array([e.x, e.y, e.z]))
                    if not (0 <= nl[0] <= 1 and 0 <= nl[1] <= 1 and 0 <= nl[2] <= 1):
                        ind_to_rem.add(j)
                        break

        d = d.drop(d.index[list(ind_to_rem)])

        meas_map_sensor = {}
        for meas_id, e_id in ms.meas_map.items():
            # todo: prepsat nejak inteligentneji
            if (meas_id not in [v for v in d["ca"]]) and (meas_id not in [v for v in d["cb"]]) and (meas_id not in [v for v in d["pa"]]) and (meas_id not in [v for v in d["pb"]]):
                continue

            ind = -1
            for j, e in enumerate(electrodes):
                if e.id == e_id:
                    ind = j
                    break
            if ind < 0:
                e = _find_el(electrode_groups, e_id)
                if e is None:
                    print("chyba")
                ind = len(electrodes)
                electrodes.append(e)
                s_id = data.createSensor([e.x, e.y, e.z])
                sensor_ids.append(s_id)
            meas_map_sensor[meas_id] = sensor_ids[ind]

        a = a.append(pd.Series([meas_map_sensor[v] for v in d["ca"]]), ignore_index=True)
        b = b.append(pd.Series([meas_map_sensor[v] for v in d["cb"]]), ignore_index=True)
        m = m.append(pd.Series([meas_map_sensor[v] for v in d["pa"]]), ignore_index=True)
        n = n.append(pd.Series([meas_map_sensor[v] for v in d["pb"]]), ignore_index=True)
        i = i.append(d["I"], ignore_index=True)
        u = u.append(d["V"], ignore_index=True)
        err = err.append(d["std"], ignore_index=True)
        rhoa = rhoa.append(d["AppRes"], ignore_index=True)

        #el_offset += len(ms.meas_map)

        for j in d.index:
            meas_info.items.append(MeasurementInfoItem(measurement_number=ms.number,
                                                       ca=d["ca"][j], cb=d["cb"][j], pa=d["pa"][j], pb=d["pb"][j],
                                                       I=d["I"][j], V=d["V"][j], AppRes=d["AppRes"][j], std=d["std"][j],
                                                       inv_ca=meas_map_sensor[d["ca"][j]], inv_cb=meas_map_sensor[d["cb"][j]], inv_pa=meas_map_sensor[d["pa"][j]], inv_pb=meas_map_sensor[d["pb"][j]]))

    data.resize(len(a))
    data.set('a', a)
    data.set('b', b)
    data.set('m', m)
    data.set('n', n)
    data.set('i', i)
    data.set('u', u)
    data.set('err', err)
    data.set('rhoa', rhoa)
    #data.markValid(data('rhoa') > 0)
    # zakomentovano kvuli analyse_measurement_dialog.py

    return data, meas_info


def _find_el(electrode_groups, e_id):
    # todo: better solution is create map
    for eg in electrode_groups:
        for e in eg.electrodes:
            if e.id == e_id:
                return e
    return None
