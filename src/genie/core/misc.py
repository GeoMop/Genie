import math


import pygimli as pg


TOLERANCE = 1e-12


def geometricFactors(data):
    """
    Returns geometric factors k for given data container.
    :param data: ERT data container
    :return: geometric factors k
    """
    k = pg.core.RVector(data.size())

    for i in range(k.size()):
        uam = ubm = uan = ubn = 0.0

        a = data("a")[i]
        b = data("b")[i]
        m = data("m")[i]
        n = data("n")[i]

        if a > -1 and m > -1:
            uam = exactDCSolution(data.sensorPosition(a), data.sensorPosition(m))
        if b > -1 and m > -1:
            ubm = exactDCSolution(data.sensorPosition(b), data.sensorPosition(m))
        if a > -1 and n > -1:
            uan = exactDCSolution(data.sensorPosition(a), data.sensorPosition(n))
        if b > -1 and n > -1:
            ubn = exactDCSolution(data.sensorPosition(b), data.sensorPosition(n))

        k[i] = 1.0 / (uam - ubm - uan + ubn)

    return k


def exactDCSolution(v, source):
    r = v.dist(source)

    if (r < TOLERANCE):
        return 1.0

    return 1.0 / (4.0 * math.pi * r)
