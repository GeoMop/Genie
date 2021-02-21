from bgem.gmsh.gmsh_io import GmshIO
from bgem.bspline import brep_writer as bw
from .cut_point_cloud import cut_tool_to_gen_vecs, inv_tr
from genie.core.data_types import MeshFrom

import numpy as np

# fix brep_writer
bw.scalar_types = (int, float, np.int32, np.int64, np.float64)


def gen(gallery_mesh_file, out_brep_file, mesh_cut_tool_param, inv_par, project_conf):
    el_char_len = 1.0
    other_char_len = 10.0

    if inv_par.meshFrom == MeshFrom.GALLERY_CLOUD:
        offset = np.array([project_conf.point_cloud_origin_x,
                           project_conf.point_cloud_origin_y,
                           project_conf.point_cloud_origin_z])
    else:
        offset = np.array([project_conf.gallery_mesh_origin_x,
                           project_conf.gallery_mesh_origin_y,
                           project_conf.gallery_mesh_origin_z])


    gallery_mesh = GmshIO(gallery_mesh_file)

    #gallery_origin = np.array(gallery_origin)

    for id, node in gallery_mesh.nodes.items():
        gallery_mesh.nodes[id] = gallery_mesh.nodes[id] #+ np.array([-622000.0, -1128000.0, 0.0])

    base_point, gen_vecs = cut_tool_to_gen_vecs(mesh_cut_tool_param)

    opposite_pont = base_point + gen_vecs[0] + gen_vecs[1] + gen_vecs[2]
    planes = [
        (base_point, gen_vecs[0], gen_vecs[1]),
        (base_point, gen_vecs[1], gen_vecs[2]),
        (base_point, gen_vecs[2], gen_vecs[0]),
        (opposite_pont, gen_vecs[0], -gen_vecs[1]),
        (opposite_pont, gen_vecs[1], -gen_vecs[2]),
        (opposite_pont, gen_vecs[2], -gen_vecs[0])]

    b = inv_tr(gen_vecs)

    class VertInfo:
        def __init__(self, node):
            self.plane_pos = [0] * 6
            self.cut = [False] * 6

            for i in range(6):
                pv = np.cross(planes[i][1], planes[i][2])
                w = np.array(node) - planes[i][0]
                self.plane_pos[i] = np.sign(np.dot(pv, w)) # sign zbytecny

    #v1 = bw.Vertex(base_point + gen_vecs[0])
    bw_vertices = {}
    vertices_tr = {}
    vert_info = {}
    for id, node in gallery_mesh.nodes.items():
        node += offset
        #bw_vertices[id] = bw.Vertex(node + np.array([- 622000, - 1128000, 0]), tolerance=1e-3)
        bw_vertices[id] = bw.Vertex(node, tolerance=1e-3)
        vert_info[id] = VertInfo(node)
        vertices_tr[id] = b @ (np.array(node) - base_point)

    bw_edges = {}

    def get_edge(id0, id1):
        k = (id0, id1)
        if k in bw_edges:
            return bw_edges[k]
        elif (id1, id0) in bw_edges:
            return bw_edges[(id1, id0)].m()
        else:
            e = bw.Edge([bw_vertices[k[0]], bw_vertices[k[1]]])
            bw_edges[k] = e
            return e

    bw_faces = []
    vids_to_move = [[], [], [], [], [], []]
    plane_edges = [[], [], [], [], [], []]
    cut_triangles = [[], [], [], [], [], []]
    tri_map = {}

    def process_triangle(id0, id1, id2):
        for i in range(6):
            if vert_info[id0].plane_pos[i] <= 0 or vert_info[id1].plane_pos[i] <= 0 or vert_info[id2].plane_pos[i] <= 0:
                id_out = set()
                for j in range(6):
                    if j == i:
                        continue
                    # todo: zbytecne resi protilehlou stranu
                    for k in [id0, id1, id2]:
                        if vert_info[k].plane_pos[j] <= 0:
                            id_out.add(k)
                if len(id_out) >= 3:
                    return
                id_inside = []
                for j in [id0, id1, id2]:
                    if vert_info[j].plane_pos[i] > 0:
                        vids_to_move[i].append(j)
                        id_inside.append(j)
                if len(id_inside) == 2:
                    edge = (id_inside[0], id_inside[1])
                    if edge in plane_edges[i]:
                        plane_edges[i].remove(edge)
                    elif (edge[1], edge[0]) in plane_edges[i]:
                        plane_edges[i].remove((edge[1], edge[0]))
                    else:
                        plane_edges[i].append(edge)
                if len(id_inside) >= 1:
                    cut_triangles[i].append((id0, id1, id2))
                return

        e1 = get_edge(id0, id1)
        e2 = get_edge(id1, id2)
        e3 = get_edge(id2, id0)
        f = bw.Face([e1, e2, e3])
        bw_faces.append(f)
        tri_map[(id0, id1, id2)] = f

    for id, data in gallery_mesh.elements.items():
        el_type, tags, nodes = data
        if el_type != 2:
            continue
        process_triangle(*nodes)

    # remove duplicit vertices id
    vids_to_move_set = [set() for _ in range(6)]
    for i in range(6):
        vids_to_move_set[i] = set(vids_to_move[i])
        vids_to_move[i] = list(vids_to_move_set[i])

    # check if every border vertex belongs to only one plane
    for i in range(6):
        for j in range(6):
            if i == j:
                continue
            if not vids_to_move_set[i].isdisjoint(vids_to_move_set[j]):
                print("ERROR: Edge of cut body is to close to gallery mesh.")
                return False

    # remove triangles laying on plane
    for i in range(6):
        two_side = []
        for id, data in gallery_mesh.elements.items():
            el_type, tags, nodes = data
            if el_type != 2:
                continue
            count = 0
            for n in nodes:
                if n in vids_to_move_set[i]:
                    count += 1
            if count == 3:
                two_side.append((*nodes, ))

                if (nodes[0], nodes[1]) in plane_edges[i]:
                    plane_edges[i].remove((nodes[0], nodes[1]))
                elif (nodes[1], nodes[0]) in plane_edges[i]:
                    plane_edges[i].remove((nodes[1], nodes[0]))
                else:
                    plane_edges[i].append((nodes[0], nodes[1]))

                if (nodes[1], nodes[2]) in plane_edges[i]:
                    plane_edges[i].remove((nodes[1], nodes[2]))
                elif (nodes[2], nodes[1]) in plane_edges[i]:
                    plane_edges[i].remove((nodes[2], nodes[1]))
                else:
                    plane_edges[i].append((nodes[1], nodes[2]))

                if (nodes[2], nodes[0]) in plane_edges[i]:
                    plane_edges[i].remove((nodes[2], nodes[0]))
                elif (nodes[0], nodes[2]) in plane_edges[i]:
                    plane_edges[i].remove((nodes[0], nodes[2]))
                else:
                    plane_edges[i].append((nodes[2], nodes[0]))

                bw_faces.remove(tri_map[(*nodes, )])

    # move border vertices
    ax_pos = [
        (2, 0.0),
        (0, 0.0),
        (1, 0.0),
        (2, 1.0),
        (0, 1.0),
        (1, 1.0),
    ]
    for i in range(6):
        for vid in vids_to_move[i]:
            shift = ax_pos[i][1] - vertices_tr[vid][ax_pos[i][0]]
            vertices_tr[vid][ax_pos[i][0]] = ax_pos[i][1]
            bw_vertices[vid].point += shift * gen_vecs[ax_pos[i][0]]


    face_edges = [[], [], [], [], [], []]

    # todo: doresit dotekajici se wiry
    for i in range(6):
        if not plane_edges[i]:
            continue
        first_edge = last_edge = plane_edges[i].pop()
        first_vertex = last_edge[0]
        last_vertex = last_edge[1]
        wire = [first_edge]
        while plane_edges[i]:
            find = False
            cont_edges = []
            for edge in list(plane_edges[i]):
                if last_vertex in edge:
                    cont_edges.append(edge)
            if cont_edges:
                # find appropriate edge
                edge = cont_edges[0]
                wire.append(edge)
                plane_edges[i].remove(edge)
                if first_vertex in edge:
                    # we have closed wire
                    face_edges[i].append(wire)
                    #print(wire)
                    if not plane_edges[i]:
                        break
                    first_edge = last_edge = plane_edges[i].pop()
                    first_vertex = last_edge[0]
                    last_vertex = last_edge[1]
                    wire = [first_edge]
                else:
                    last_edge = edge
                    last_vertex = edge[1] if last_vertex != edge[1] else edge[0]
            else:
                # not find closed wire
                if not plane_edges[i]:
                    break
                first_edge = last_edge = plane_edges[i].pop()
                first_vertex = last_edge[0]
                last_vertex = last_edge[1]
                wire = [first_edge]

    v1 = bw.Vertex(base_point + gen_vecs[0])
    v2 = bw.Vertex(base_point + gen_vecs[2] + gen_vecs[0])
    v3 = bw.Vertex(base_point + gen_vecs[2] + gen_vecs[1] + gen_vecs[0])
    v4 = bw.Vertex(base_point + gen_vecs[1] + gen_vecs[0])

    v5 = bw.Vertex(base_point)
    v6 = bw.Vertex(base_point + gen_vecs[2])
    v7 = bw.Vertex(base_point + gen_vecs[2] + gen_vecs[1])
    v8 = bw.Vertex(base_point + gen_vecs[1])

    e1 = bw.Edge([v1, v2])
    e2 = bw.Edge([v2, v3])
    e3 = bw.Edge([v3, v4])
    e4 = bw.Edge([v4, v1])


    faces = []
    for i in [4]:#range(6):
        #surf, vtxs_uv = bw.Approx.plane([planes[i][0], planes[i][0] + planes[i][1], planes[i][0] + planes[i][2]])
        surf, vtxs_uv = bw.Approx.plane([v1.point, v1.point + gen_vecs[1], v1.point + gen_vecs[2]])
        assert vtxs_uv == [(0, 0), (1, 0), (0, 1)]

        e1.attach_to_surface(surf, (0, 0), (0, 1) )
        e2.attach_to_surface(surf, (0, 1), (1, 1) )
        e3.attach_to_surface(surf, (1, 1), (1, 0) )
        e4.attach_to_surface(surf, (1, 0), (0, 0) )

        for j in range(len(face_edges[i])):
            for e in face_edges[i][j]:
                try:
                    bw_edges[e].attach_to_surface(surf, vertices_tr[e[0]][1:], vertices_tr[e[1]][1:])
                except KeyError:
                    bw_edges[(e[1], e[0])].attach_to_surface(surf, vertices_tr[e[1]][1:], vertices_tr[e[0]][1:])

        wire_list = []
        for j in range(len(face_edges[i])):
            edge_list = []
            for e in face_edges[i][j]:
                if e in bw_edges:
                    edge_list.append(bw_edges[e])
                else:
                    edge_list.append(bw_edges[(e[1], e[0])])
            wire_list.append(edge_list)
        # todo: face v dire nefunguje
        faces.append(bw.Face([bw.Wire([e1, e2, e3, e4]), *[bw.Wire(edge_list) for edge_list in wire_list]], surface=surf))

    #f1 = bw.Face([bw.Wire([e1, e2, e3]), bw.Wire([e1x, e2x, e3x])], surface=surf)

    e5 = bw.Edge([v5, v6])
    e6 = bw.Edge([v6, v7])
    e7 = bw.Edge([v7, v8])
    e8 = bw.Edge([v8, v5])

    f2 = bw.Face([e5, e6, e7, e8])

    e9 = bw.Edge([v1, v5])
    e10 = bw.Edge([v2, v6])
    e11 = bw.Edge([v3, v7])
    e12 = bw.Edge([v4, v8])

    # f3 = bw.Face([e1, e10, e5.m(), e9.m()])
    # f4 = bw.Face([e2, e11, e6.m(), e10.m()])
    # f5 = bw.Face([e3, e12, e7.m(), e11.m()])
    # f6 = bw.Face([e4, e9, e8.m(), e12.m()])

    for i in [2]:#range(6):
        surf, vtxs_uv = bw.Approx.plane([v5.point, v5.point + gen_vecs[0], v5.point + gen_vecs[2]])
        assert vtxs_uv == [(0, 0), (1, 0), (0, 1)]

        e1.attach_to_surface(surf, (1, 0), (1, 1) )
        e10.attach_to_surface(surf, (1, 1), (0, 1) )
        e5.attach_to_surface(surf, (0, 0), (0, 1) )
        e9.attach_to_surface(surf, (1, 0), (0, 0) )

        for j in range(len(face_edges[i])):
            for e in face_edges[i][j]:
                try:
                    bw_edges[e].attach_to_surface(surf, vertices_tr[e[0]][0:3:2], vertices_tr[e[1]][0:3:2])
                except KeyError:
                    bw_edges[(e[1], e[0])].attach_to_surface(surf, vertices_tr[e[1]][0:3:2], vertices_tr[e[0]][0:3:2])

        wire_list = []
        for j in range(len(face_edges[i])):
            edge_list = []
            for e in face_edges[i][j]:
                if e in bw_edges:
                    edge_list.append(bw_edges[e])
                else:
                    edge_list.append(bw_edges[(e[1], e[0])])
            wire_list.append(edge_list)
        faces.append(bw.Face([bw.Wire([e1, e10, e5, e9]), *[bw.Wire(edge_list) for edge_list in wire_list]], surface=surf))


    for i in [5]:#range(6):
        surf, vtxs_uv = bw.Approx.plane([v8.point, v8.point + gen_vecs[0], v8.point + gen_vecs[2]])
        #print(vtxs_uv)

        e3.attach_to_surface(surf, (1, 1), (1, 0) )
        e12.attach_to_surface(surf, (1, 0), (0, 0) )
        e7.attach_to_surface(surf, (0, 1), (0, 0) )
        e11.attach_to_surface(surf, (1, 1), (0, 1) )

        for j in range(len(face_edges[i])):
            for e in face_edges[i][j]:
                try:
                    bw_edges[e].attach_to_surface(surf, vertices_tr[e[0]][0:3:2], vertices_tr[e[1]][0:3:2])
                except KeyError:
                    bw_edges[(e[1], e[0])].attach_to_surface(surf, vertices_tr[e[1]][0:3:2], vertices_tr[e[0]][0:3:2])

        wire_list = []
        for j in range(len(face_edges[i])):
            edge_list = []
            for e in face_edges[i][j]:
                if e in bw_edges:
                    edge_list.append(bw_edges[e])
                else:
                    edge_list.append(bw_edges[(e[1], e[0])])
            wire_list.append(edge_list)

        #wire_list2 = [wire_list[4]]
        #wire_list.remove(wire_list[4])

        faces.append(bw.Face([bw.Wire([e3, e12, e7, e11]), *[bw.Wire(edge_list) for edge_list in wire_list]], surface=surf))
        #faces.append(bw.Face([bw.Wire(edge_list)], surface=surf))
        #faces.append(bw.Face([*[bw.Wire(edge_list) for edge_list in wire_list2]], surface=surf))


    for i in [1]:#range(6):
        surf, vtxs_uv = bw.Approx.plane([v5.point, v5.point + gen_vecs[1], v5.point + gen_vecs[2]])
        #print(vtxs_uv)

        e5.attach_to_surface(surf, (0, 0), (0, 1) )
        e6.attach_to_surface(surf, (0, 1), (1, 1) )
        e7.attach_to_surface(surf, (1, 1), (1, 0) )
        e8.attach_to_surface(surf, (1, 0), (0, 0) )

        for j in range(len(face_edges[i])):
            for e in face_edges[i][j]:
                try:
                    bw_edges[e].attach_to_surface(surf, vertices_tr[e[0]][1:], vertices_tr[e[1]][1:])
                except KeyError:
                    bw_edges[(e[1], e[0])].attach_to_surface(surf, vertices_tr[e[1]][1:], vertices_tr[e[0]][1:])

        wire_list = []
        for j in range(len(face_edges[i])):
            edge_list = []
            for e in face_edges[i][j]:
                if e in bw_edges:
                    edge_list.append(bw_edges[e])
                else:
                    edge_list.append(bw_edges[(e[1], e[0])])
            wire_list.append(edge_list)
        faces.append(bw.Face([bw.Wire([e5, e6, e7, e8]), *[bw.Wire(edge_list) for edge_list in wire_list]], surface=surf))


    for i in [3]:#range(6):
        surf, vtxs_uv = bw.Approx.plane([v6.point, v6.point + gen_vecs[0], v6.point + gen_vecs[1]])

        e2.attach_to_surface(surf, (1, 0), (1, 1) )
        e11.attach_to_surface(surf, (1, 1), (0, 1) )
        e6.attach_to_surface(surf, (0, 0), (0, 1) )
        e10.attach_to_surface(surf, (1, 0), (0, 0) )

        for j in range(len(face_edges[i])):
            for e in face_edges[i][j]:
                try:
                    bw_edges[e].attach_to_surface(surf, vertices_tr[e[0]][:2], vertices_tr[e[1]][:2])
                except KeyError:
                    bw_edges[(e[1], e[0])].attach_to_surface(surf, vertices_tr[e[1]][:2], vertices_tr[e[0]][:2])

        wire_list = []
        for j in range(len(face_edges[i])):
            edge_list = []
            for e in face_edges[i][j]:
                if e in bw_edges:
                    edge_list.append(bw_edges[e])
                else:
                    edge_list.append(bw_edges[(e[1], e[0])])
            wire_list.append(edge_list)
        faces.append(bw.Face([bw.Wire([e2, e11, e6, e10]), *[bw.Wire(edge_list) for edge_list in wire_list]], surface=surf))

    for i in [0]:#range(6):
        surf, vtxs_uv = bw.Approx.plane([v5.point, v5.point + gen_vecs[0], v5.point + gen_vecs[1]])

        e4.attach_to_surface(surf, (1, 1), (1, 0) )
        e9.attach_to_surface(surf, (1, 0), (0, 0) )
        e8.attach_to_surface(surf, (0, 1), (0, 0) )
        e12.attach_to_surface(surf, (1, 1), (0, 1) )

        for j in range(len(face_edges[i])):
            for e in face_edges[i][j]:
                try:
                    bw_edges[e].attach_to_surface(surf, vertices_tr[e[0]][:2], vertices_tr[e[1]][:2])
                except KeyError:
                    bw_edges[(e[1], e[0])].attach_to_surface(surf, vertices_tr[e[1]][:2], vertices_tr[e[0]][:2])

        wire_list = []
        for j in range(len(face_edges[i])):
            edge_list = []
            for e in face_edges[i][j]:
                if e in bw_edges:
                    edge_list.append(bw_edges[e])
                else:
                    edge_list.append(bw_edges[(e[1], e[0])])
            wire_list.append(edge_list)
        faces.append(bw.Face([bw.Wire([e4, e9, e8, e12]), *[bw.Wire(edge_list) for edge_list in wire_list]], surface=surf))

    shell = bw.Shell(bw_faces + faces)
    #shell = bw.Shell(faces)

    s1 = bw.Solid([shell])

    c1 = bw.Compound([s1])

    with open(out_brep_file, "w") as f:
        bw.write_model(f, c1)

    return True
