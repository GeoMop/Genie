from bgem.gmsh.gmsh_io import GmshIO
import bih
import pygimli as pg

import numpy as np
import time

from genie.core.data_types import MeshFrom
from genie.core.global_const import GenieMethod


def main(inv_par, project_conf, max_dist=1.0, final=False):
    if inv_par.meshFrom == MeshFrom.GALLERY_CLOUD:
        mesh_file = "gallery_mesh.msh"
        offset = np.array([project_conf.point_cloud_origin_x,
                           project_conf.point_cloud_origin_y,
                           project_conf.point_cloud_origin_z])
    elif inv_par.meshFrom == MeshFrom.SURFACE_CLOUD:
        mesh_file = "inv_mesh_tmp.msh2"
        offset = np.array( [0.0, 0.0, 0.0])
    else:
        mesh_file = "../../gallery_mesh.msh"
        offset = np.array([project_conf.gallery_mesh_origin_x,
                           project_conf.gallery_mesh_origin_y,
                           project_conf.gallery_mesh_origin_z])

    if final:
        mesh_file = "inv_mesh_tmp.msh2"
        offset = np.array( [0.0, 0.0, 0.0])

    mesh = GmshIO(mesh_file)

    #mesh.elements = {id: data for id, data in mesh.elements.items() if id not in [714, 2095]}

    tree = bih.BIH()
    boxes = []
    mesh.elements2 = {}
    i = 0
    for data in mesh.elements.values():
        type_, tags, nodeIDs = data
        if type_ != 2:
            continue
        # a = np.array(mesh.nodes[nodeIDs[0]]) + np.array([-622000.0, -1128000.0, 0.0])
        # b = np.array(mesh.nodes[nodeIDs[1]]) + np.array([-622000.0, -1128000.0, 0.0])
        # c = np.array(mesh.nodes[nodeIDs[2]]) + np.array([-622000.0, -1128000.0, 0.0])
        # a = np.array(mesh.nodes[nodeIDs[0]])
        # b = np.array(mesh.nodes[nodeIDs[1]])
        # c = np.array(mesh.nodes[nodeIDs[2]])
        a = np.array(mesh.nodes[nodeIDs[0]]) + offset
        b = np.array(mesh.nodes[nodeIDs[1]]) + offset
        c = np.array(mesh.nodes[nodeIDs[2]]) + offset
        boxes.append(bih.AABB([a, b, c]))
        mesh.elements2[i] = data
        i += 1


    tree.add_boxes(boxes)
    tree.construct()

    # electrodes = []
    # with open("electrodes_small.xyz") as fd:
    #     for i, line in enumerate(fd):
    #         s = line.split()
    #         if len(s) >= 3:
    #             el = np.array([float(s[0]), float(s[1]), float(s[2])])
    #             electrodes.append(el)
    #
    # t = time.time()
    # snapped_electrodes = [snap_electrode(el, mesh, tree) for el in electrodes]
    # print("elapsed time = {:.3f} s".format(time.time() - t))
    #
    # with open("electrodes_small_snapped2.xyz", "w") as fd:
    #     for el in snapped_electrodes:
    #         fd.write("{} {} {}\n".format(el[0], el[1], el[2]))

    if project_conf.method == GenieMethod.ERT:
        data = pg.DataContainerERT("input.dat", removeInvalid=False)
    else:
        data = pg.DataContainer("input.dat", sensorTokens='s g', removeInvalid=False)

    for i in range(len(data.sensorPositions())):
        pos = data.sensorPosition(i)
        pos = np.array([pos[0], pos[1], pos[2]])
        new_pos = snap_electrode(pos, mesh, tree, max_dist, offset)

        data.setSensorPosition(i, new_pos)
    data.save("input_snapped.dat")


def snap_electrode(electrode, mesh, tree, max_dist, offset):
    dist_min = np.inf
    pos_min = electrode

    #intersect_box_ids = tree.find_point(electrode)

    box = bih.AABB([electrode - max_dist, electrode + max_dist])
    intersect_box_ids = tree.find_box(box)


    #for id, data in mesh.elements.items():
    for id in intersect_box_ids:
        data = mesh.elements2[id]
        el_type, tags, nodes = data
        if el_type != 2:
            continue
        # a = np.array(mesh.nodes[nodes[0]]) + np.array([-622000.0, -1128000.0, 0.0])
        # b = np.array(mesh.nodes[nodes[1]]) + np.array([-622000.0, -1128000.0, 0.0])
        # c = np.array(mesh.nodes[nodes[2]]) + np.array([-622000.0, -1128000.0, 0.0])
        # a = np.array(mesh.nodes[nodes[0]])
        # b = np.array(mesh.nodes[nodes[1]])
        # c = np.array(mesh.nodes[nodes[2]])
        a = np.array(mesh.nodes[nodes[0]]) + offset
        b = np.array(mesh.nodes[nodes[1]]) + offset
        c = np.array(mesh.nodes[nodes[2]]) + offset
        dist, snapped_electrode = tri_point_dist(a, b, c, electrode)
        if dist < dist_min and dist <= max_dist:
            dist_min = dist
            pos_min = snapped_electrode

    return pos_min


count = 0
def tri_point_dist(a, b, c, p):
    global count
    count += 1

    ab = b - a
    ac = c - a
    tr = np.array([ab, ac, np.cross(ab, ac)]).T
    inv_tr = np.linalg.inv(tr)
    loc = inv_tr @ (p - a)
    beta = loc[0]
    gama = loc[1]
    alpha = 1 - beta - gama

    def ret_fun(snapped_p):
        return np.linalg.norm(snapped_p - p), snapped_p

    if 0 <= alpha <= 1 and 0 <= beta <= 1 and 0 <= gama <= 1:
        # inside
        snapped_p = a + beta * ab + gama * ac
        return ret_fun(snapped_p)

    dab, pab = ret_fun(edge_dis(a, b, p))
    dac, pac = ret_fun(edge_dis(a, c, p))
    dbc, pbc = ret_fun(edge_dis(b, c, p))

    if dab < dac:
        if dab < dbc:
            return dab, pab
    else:
        if dac < dbc:
            return dac, pac
    return dbc, pbc


def edge_dis(a, b, p):
    delta = b - a
    t = np.dot(p - a, delta) / np.linalg.norm(delta) ** 2

    if t < 0:
        return a

    if t > 1:
        return b

    return a + t * delta


def tri_point_dist_fast_bug(a, b, c, p):
    global count
    count += 1

    ab = b - a
    ac = c - a
    tr = np.array([ab, ac, np.cross(ab, ac)]).T
    inv_tr = np.linalg.inv(tr)
    loc = inv_tr @ (p - a)
    beta = loc[0]
    gama = loc[1]
    alpha = 1 - beta - gama

    def ret_fun(snapped_p):
        return np.linalg.norm(snapped_p - p), snapped_p

    if 0 <= alpha <= 1 and 0 <= beta <= 1 and 0 <= gama <= 1:
        # inside
        snapped_p = a + beta * ab + gama * ac
        return ret_fun(snapped_p)
    elif alpha > 0 and beta <= 0 and gama <= 0:
        # a
        return ret_fun(a)
    elif alpha <= 0 and beta > 0 and gama <= 0:
        # b
        return ret_fun(b)
    elif alpha <= 0 and beta <= 0 and gama > 0:
        # c
        return ret_fun(c)
    elif alpha > 0 and beta > 0 and gama < 0:
        # ab
        return ret_fun(edge_proj(a, b, p))
    elif alpha > 0 and beta < 0 and gama > 0:
        # ac
        return ret_fun(edge_proj(a, c, p))
    elif alpha < 0 and beta > 0 and gama > 0:
        # bc
        return ret_fun(edge_proj(b, c, p))
    else:
        print("divny {}, {}, {}".format(alpha, beta, gama))

    return ret_fun(a)


def edge_proj(a, b, p):
    delta = b - a
    t = np.dot(p - a, delta) / np.linalg.norm(delta) ** 2
    return a + t * delta


if __name__ == "__main__":
    main()
    print("tri_point_dist eval: {}".format(count))
