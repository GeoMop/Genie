import pygimli as pg

import numpy as np

from genie.core.global_const import GenieMethod


def main(inv_par, project_conf, bw_surface, max_dist=1.0):
    a = bw_surface._bs_surface.eval(0, 0)
    b = bw_surface._bs_surface.eval(1, 0)
    c = bw_surface._bs_surface.eval(0, 1)

    a[2] = 0
    b[2] = 0
    c[2] = 0

    ab = b - a
    ac = c - a
    tr = np.array([ab, ac, [0, 0, 1]]).T
    inv_tr = np.linalg.inv(tr)

    if project_conf.method == GenieMethod.ERT:
        data = pg.DataContainerERT("input.dat", removeInvalid=False)
    else:
        data = pg.DataContainer("input.dat", sensorTokens='s g', removeInvalid=False)

    for i in range(len(data.sensorPositions())):
        pos = data.sensorPosition(i)
        pos = np.array([pos[0], pos[1], pos[2]])
        pos_l = inv_tr @ (pos - a)

        try:
            new_pos = bw_surface._bs_surface.eval(pos_l[0], pos_l[1])
        except IndexError:
            pass
        else:
            if np.linalg.norm(new_pos - pos) <= max_dist:
                data.setSensorPosition(i, new_pos)

    data.save("input_snapped.dat")


if __name__ == "__main__":
    main()
