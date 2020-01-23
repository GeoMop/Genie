import pandas as pd
#import pybert as pb
import pygimli as pg


def prepare(electrode_groups, measurements):
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


def _find_el(electrode_groups, e_id):
    # todo: better solution is create map
    for eg in electrode_groups:
        for e in eg.electrodes:
            if e.id == e_id:
                return e
    return None
