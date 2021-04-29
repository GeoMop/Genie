import pandas as pd
import pygimli as pg
import numpy as np

from genie.core import cut_point_cloud


def prepare(electrode_groups, measurements, first_arrivals, mesh_cut_tool_param=None, use_only_verified=False):
    """
    Prepares data for GIMLI inversion.
    :param electrode_groups:
    :param measurements:
    :return:
    """
    electrodes = []
    sensor_ids = []
    s = pd.Series()
    g = pd.Series()
    t = pd.Series()

    data = pg.DataContainer()
    data.registerSensorIndex("s")
    data.registerSensorIndex("g")

    if mesh_cut_tool_param is not None:
        base_point, gen_vecs = cut_point_cloud.cut_tool_to_gen_vecs(mesh_cut_tool_param, only_inv=True)
        inv_tr_mat = cut_point_cloud.inv_tr(gen_vecs)

    for ms in measurements:
        if ms.data is None:
            continue

        meas_map_sensor = {}
        fa_list = []

        # receivers
        if ms.receiver_stop >= ms.receiver_start:
            receivers = list(range(ms.receiver_start, ms.receiver_stop + 1))
        else:
            receivers = list(range(ms.receiver_start, ms.receiver_stop - 1, -1))

        # remove measurements outside inversion region
        if mesh_cut_tool_param is not None:
            e = _find_el(electrode_groups, ms.source_id)
            nl = cut_point_cloud.tr_to_local(base_point, inv_tr_mat, np.array([e.x, e.y, e.z]))
            if not (0 <= nl[0] <= 1 and 0 <= nl[1] <= 1 and 0 <= nl[2] <= 1):
                continue

            ind_to_rem = set()
            for j, r in enumerate(receivers):
                e = _find_el(electrode_groups, r)
                nl = cut_point_cloud.tr_to_local(base_point, inv_tr_mat, np.array([e.x, e.y, e.z]))
                if not (0 <= nl[0] <= 1 and 0 <= nl[1] <= 1 and 0 <= nl[2] <= 1):
                    ind_to_rem.add(j)

            receivers = [r for r in receivers if r not in ind_to_rem]

        receivers_used = []
        for meas_id, e_id in enumerate(receivers):
            fa = _find_fa(first_arrivals, ms.file, meas_id + ms.channel_start - 1)
            if fa is None:
                print("chyba")
                continue
            if fa.use and (fa.verified or not use_only_verified):
                if fa.verified:
                    time = fa.time
                else:
                    time = fa.time_auto
                receivers_used.append(e_id)
                fa_list.append(time)

        if not receivers_used:
            continue

        for meas_id, e_id in enumerate(receivers_used):
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

        # source
        e_id = ms.source_id
        meas_id = len(receivers_used)
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

        s = s.append(pd.Series([meas_map_sensor[len(receivers_used)]] * len(receivers_used)), ignore_index=True)
        g = g.append(pd.Series([meas_map_sensor[v] for v in range(len(receivers_used))]), ignore_index=True)
        t = t.append(pd.Series(fa_list), ignore_index=True)

    l = len(s)
    data.resize(l)
    if l > 0:
        data.set('s', s)
        data.set('g', g)
        data.set('t', t)

    return data


def _find_el(electrode_groups, e_id):
    # todo: better solution is create map
    for eg in electrode_groups:
        for e in eg.electrodes:
            if e.id == e_id:
                return e
    return None


def _find_fa(first_arrivals, file, channel):
    for fa in first_arrivals:
        if fa.file == file and fa.channel == channel:
            return fa
    return None
