from bgem.gmsh.gmsh_io import GmshIO
import bih
import pygimli as pg

import numpy as np
import time


def main(max_dist=1.0):
    mesh_file = "gallery_mesh.msh"
    mesh = GmshIO(mesh_file)

    #mesh.elements = {id: data for id, data in mesh.elements.items() if id not in [714, 2095]}

    tree = bih.BIH()
    boxes = []
    mesh.elements2 = {}
    for i, data in enumerate(mesh.elements.values()):
        type_, tags, nodeIDs = data
        a = np.array(mesh.nodes[nodeIDs[0]]) + np.array([-622000.0, -1128000.0, 0.0])
        b = np.array(mesh.nodes[nodeIDs[1]]) + np.array([-622000.0, -1128000.0, 0.0])
        c = np.array(mesh.nodes[nodeIDs[2]]) + np.array([-622000.0, -1128000.0, 0.0])
        # a = np.array(mesh.nodes[nodeIDs[0]])
        # b = np.array(mesh.nodes[nodeIDs[1]])
        # c = np.array(mesh.nodes[nodeIDs[2]])
        boxes.append(bih.AABB([a, b, c]))
        mesh.elements2[i] = data


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

    data = pg.DataContainerERT("input.dat", removeInvalid=False)
    for i in range(len(data.sensorPositions())):
        pos = data.sensorPosition(i)
        pos = np.array([pos[0], pos[1], pos[2]])
        new_pos = snap_electrode(pos, mesh, tree, max_dist)

        data.setSensorPosition(i, new_pos)
    data.save("input_snapped.dat")


def snap_electrode(electrode, mesh, tree, max_dist):
    dist_min = np.inf
    pos_min = electrode

    #intersect_box_ids = tree.find_point(electrode)

    box = bih.AABB([electrode - max_dist, electrode + max_dist])
    intersect_box_ids = tree.find_box(box)


    #for id, data in mesh.elements.items():
    for id in intersect_box_ids:
        data = mesh.elements2[id]
        el_type, tags, nodes = data
        a = np.array(mesh.nodes[nodes[0]]) + np.array([-622000.0, -1128000.0, 0.0])
        b = np.array(mesh.nodes[nodes[1]]) + np.array([-622000.0, -1128000.0, 0.0])
        c = np.array(mesh.nodes[nodes[2]]) + np.array([-622000.0, -1128000.0, 0.0])
        # a = np.array(mesh.nodes[nodes[0]])
        # b = np.array(mesh.nodes[nodes[1]])
        # c = np.array(mesh.nodes[nodes[2]])
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

    if 0 <= alpha <= 1 and 0 <= beta <= 1 and 0 <= gama <= 1:
        # inside
        snapped_p = a + beta * ab + gama * ac
        return np.linalg.norm(snapped_p - p), snapped_p
    elif alpha > 0 and beta <= 0 and gama <= 0:
        # a
        return np.linalg.norm(a - p), a
    elif alpha <= 0 and beta > 0 and gama <= 0:
        # b
        return np.linalg.norm(b - p), b
    elif alpha <= 0 and beta <= 0 and gama > 0:
        # c
        return np.linalg.norm(c - p), c
    elif alpha > 0 and beta > 0 and gama < 0:
        # ab
        edge_proj(a, b, p)
    elif alpha > 0 and beta < 0 and gama > 0:
        # ac
        edge_proj(a, c, p)
    elif alpha < 0 and beta > 0 and gama > 0:
        # bc
        edge_proj(b, c, p)
    else:
        print("divny {}, {}, {}".format(alpha, beta, gama))

    return np.linalg.norm(a - p), a
    #return dist, snapped_p


def edge_proj(a, b, p):
    delta = b - a
    t = np.dot(p - a, delta) / np.linalg.norm(delta) ** 2
    return a + t * delta


if __name__ == "__main__":
    main()
    print("tri_point_dist eval: {}".format(count))
