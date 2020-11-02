import pandas as pd
import pygimli as pg


def prepare(electrode_groups, measurements, first_arrivals):
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

        receivers_used = []
        for meas_id, e_id in enumerate(receivers):
            fa = _find_fa(first_arrivals, ms.file, meas_id + ms.channel_start - 1)
            if fa is None:
                print("chyba")
                continue
            if fa.use:
                receivers_used.append(e_id)
                fa_list.append(fa.time)

        if not receivers_used:
            continue

        for meas_id, e_id in enumerate(receivers_used):
            ind = -1
            for j, e in enumerate(electrodes):
                if e.id == e_id and e.is_receiver:
                    ind = j
                    break
            if ind < 0:
                e = _find_el(electrode_groups, e_id, True)
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
            if e.id == e_id and not e.is_receiver:
                ind = j
                break
        if ind < 0:
            e = _find_el(electrode_groups, e_id, False)
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


def _find_el(electrode_groups, e_id, is_receiver):
    # todo: better solution is create map
    for eg in electrode_groups:
        for e in eg.electrodes:
            if e.id == e_id and e.is_receiver == is_receiver:
                return e
    return None


def _find_fa(first_arrivals, file, channel):
    for fa in first_arrivals:
        if fa.file == file and fa.channel == channel:
            return fa
    return None
