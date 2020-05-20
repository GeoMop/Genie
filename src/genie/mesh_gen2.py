from bgem.gmsh.gmsh_io import GmshIO
from bgem.bspline import brep_writer as bw
from cut_point_cloud import cut_tool_to_gen_vecs

import numpy as np

# fix brep_writer
bw.scalar_types = (int, float, np.int32, np.int64, np.float64)


def gen(mesh_cut_tool_param):
    mesh_file = "gallery_mesh.msh"
    mesh = GmshIO(mesh_file)

    for id, node in mesh.nodes.items():
        mesh.nodes[id] = mesh.nodes[id] #+ np.array([-622000.0, -1128000.0, 0.0])

    #box = [[-380.19, -955.53, 14.92], [-280.19, -905.53, 34.92]]
    box = [[-330.19, -935.53, 14.92], [-280.19, -905.53, 34.92]]

    base_point = np.array(box[0])
    gen_vecs = [np.array([box[1][0] - box[0][0], 0, 0]), np.array([0, box[1][1] - box[0][1], 0]), np.array([0, 0, box[1][2] - box[0][2]])]

    base_point = np.array([-335.69597159163095, -942.8315976371523, 10])
    gen_vecs = [np.array([30.71235975017771, 10.193751493701711, 0]), np.array([-4.870347935939208, 23.058125448180363, 0]), np.array([0, 0, 30])]

    base_point = np.array([-359.3151459915098 - 622340, -830.5880627848674 - 1128940, 10])
    gen_vecs = [np.array([40.0, -0.0, 0]), np.array([0.0, 20.0, 0]), np.array([0, 0, 30])]

    base_point = np.array([-364.88 - 622000, -829.73 - 1128000, 10])
    gen_vecs = [np.array([35, -0.0, 0]), np.array([0.0, 20.0, 0]), np.array([0, 0, 30])]

    # base_point = np.array([-364.88 , -829.73, 10])
    # gen_vecs = [np.array([10, -0.0, 0]), np.array([0.0, 20.0, 0]), np.array([0, 0, 30])]

    base_point, gen_vecs = cut_tool_to_gen_vecs(mesh_cut_tool_param)
    base_point[0] += - 622000
    base_point[1] += - 1128000
    print("#####################")
    print(base_point)


    opposite_pont = base_point + gen_vecs[0] + gen_vecs[1] + gen_vecs[2]
    planes = [
        (base_point, gen_vecs[0], gen_vecs[1]),
        (base_point, gen_vecs[1], gen_vecs[2]),
        (base_point, gen_vecs[2], gen_vecs[0]),
        (opposite_pont, gen_vecs[0], -gen_vecs[1]),
        (opposite_pont, gen_vecs[1], -gen_vecs[2]),
        (opposite_pont, gen_vecs[2], -gen_vecs[0])]

    a = np.array(gen_vecs).T
    #a = np.concatenate(gen_vecs, axis=0)
    #a = np.array([[gen_vecs[0][0], gen_vecs[1][0], gen_vecs[2][0]], [gen_vecs[0][1], gen_vecs[1][1], gen_vecs[2][1]], [gen_vecs[0][2], gen_vecs[1][2], gen_vecs[2][2]]])
    print(a)
    b = np.linalg.inv(a)
    print(b)

    class VertInfo:
        def __init__(self, node):
            self.plane_pos = [0] * 6
            self.cut = [False] * 6

            for i in range(6):
                pv = np.cross(planes[i][1], planes[i][2])
                w = np.array(node) - planes[i][0]
                self.plane_pos[i] = np.sign(np.dot(pv, w)) # sign zbytecny

    bw_vertices = {}
    vertices_tr = {}
    bw_vertices_yz = {}
    vert_info = {}
    for id, node in mesh.nodes.items():
        node += np.array([- 622000, - 1128000, 0])
        #bw_vertices[id] = bw.Vertex(node + np.array([- 622000, - 1128000, 0]), tolerance=1e-3)
        bw_vertices[id] = bw.Vertex(node, tolerance=1e-3)
        #print(node + np.array([- 622000, - 1128000, 0]))
        bw_vertices_yz[id] = node[1:]
        vert_info[id] = VertInfo(node)
        vertices_tr[id] = b @ (np.array(node) - base_point)

    print(bw_vertices[1].point)
    print(vertices_tr[1])
    print(a@vertices_tr[1]+base_point)



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

    def add_triangle(id0, id1, id2):
        for i in range(6):
            if vert_info[id0].plane_pos[i] < 0 or vert_info[id1].plane_pos[i] < 0 or vert_info[id2].plane_pos[i] < 0:
                for j in [id0, id1, id2]:
                    if vert_info[j].plane_pos[i] >= 0:
                        vids_to_move[i].append(j)
                return

        e1 = get_edge(id0, id1)
        e2 = get_edge(id1, id2)
        e3 = get_edge(id2, id0)
        f = bw.Face([e1, e2, e3])
        bw_faces.append(f)

    for id, data in mesh.elements.items():
        type_, tags, nodeIDs = data
        #print(nodeIDs)
        add_triangle(*nodeIDs)

    for i in range(6):
        vids_to_move[i] = list(set(vids_to_move[i]))

    ax_pos = [
        (2, box[0][2], 0.0),
        (0, box[0][0], 0.0),
        (1, box[0][1], 0.0),
        (2, box[1][2], 1.0),
        (0, box[1][0], 1.0),
        (1, box[1][1], 1.0),
    ]
    for i in range(6):
        for vid in vids_to_move[i]:
            #bw_vertices[vid].point[ax_pos[i][0]] = ax_pos[i][1]
            shift = ax_pos[i][2] - vertices_tr[vid][ax_pos[i][0]]
            vertices_tr[vid][ax_pos[i][0]] = ax_pos[i][2]
            bw_vertices[vid].point += shift * gen_vecs[ax_pos[i][0]]

    face_edges = [[], [], [], [], [], []]
    face_edges_yz = [[], [], [], [], [], []]
    face_edges_xz = [[], [], [], [], [], []]
    face_edges_xy = [[], [], [], [], [], []]
    for i in [1, 2, 4, 5]:#range(6):
        if not vids_to_move[i]:
            continue
        first = last = vids_to_move[i].pop()
        #face_edges_xz = []
        while vids_to_move[i]:
            find = False
            for id in list(vids_to_move[i]):
                if (last, id) in bw_edges:
                    face_edges[i].append(bw_edges[(last, id)])
                    #face_edges_yz.append((bw_vertices_yz[last], bw_vertices_yz[id]))
                    face_edges_yz[i].append((vertices_tr[last][1:], vertices_tr[id][1:]))
                    face_edges_xz[i].append((vertices_tr[last][0:3:2], vertices_tr[id][0:3:2]))
                    face_edges_xy[i].append((vertices_tr[last][:2], vertices_tr[id][:2]))
                    vids_to_move[i].remove(id)
                    last = id
                    find = True
                    break
                if (id, last) in bw_edges:
                    face_edges[i].append(bw_edges[(id, last)].m())
                    #face_edges_yz.append((bw_vertices_yz[last], bw_vertices_yz[id]))
                    face_edges_yz[i].append((vertices_tr[last][1:], vertices_tr[id][1:]))
                    face_edges_xz[i].append((vertices_tr[last][0:3:2], vertices_tr[id][0:3:2]))
                    face_edges_xy[i].append((vertices_tr[last][:2], vertices_tr[id][:2]))
                    vids_to_move[i].remove(id)
                    last = id
                    find = True
                    break
            if not find:
                print("nenasel!!!!!!!!!!!!")
                break
        #print(vids_to_move)
        if (last, first) in bw_edges:
            face_edges[i].append(bw_edges[(last, first)])
            #face_edges_yz.append((bw_vertices_yz[last], bw_vertices_yz[first]))
            face_edges_yz[i].append((vertices_tr[last][1:], vertices_tr[last][1:]))
            face_edges_xz[i].append((vertices_tr[last][0:3:2], vertices_tr[last][0:3:2]))
            face_edges_xy[i].append((vertices_tr[last][:2], vertices_tr[last][:2]))
        elif (first, last) in bw_edges:
            face_edges[i].append(bw_edges[(first, last)].m())
            #face_edges_yz.append((bw_vertices_yz[last], bw_vertices_yz[first]))
            face_edges_yz[i].append((vertices_tr[last][1:], vertices_tr[first][1:]))
            face_edges_xz[i].append((vertices_tr[last][0:3:2], vertices_tr[first][0:3:2]))
            face_edges_xy[i].append((vertices_tr[last][0:3:2], vertices_tr[first][0:3:2]))
    print(len(face_edges[4]))
    # import sys
    # sys.exit()
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
        #surf, vtxs_uv = bw.Approx.plane([(box[1][0], 0, 0), (box[1][0], 1, 0), (box[1][0], 0, 1)])
        #surf, vtxs_uv = bw.Approx.plane([planes[i][0], planes[i][0] + planes[i][1], planes[i][0] + planes[i][2]])
        surf, vtxs_uv = bw.Approx.plane([v1.point, v1.point + gen_vecs[1], v1.point + gen_vecs[2]])
        print(vtxs_uv)
        # e1.attach_to_plane(surf, (box[0][1], box[0][2]), (box[0][1], box[1][2]) )
        # e2.attach_to_plane(surf, (box[0][1], box[1][2]), (box[1][1], box[1][2]) )
        # e3.attach_to_plane(surf, (box[1][1], box[1][2]), (box[1][1], box[0][2]) )
        # e4.attach_to_plane(surf, (box[1][1], box[0][2]), (box[0][1], box[0][2]) )
        #
        # for j, e in enumerate(face_edges[i]):
        #     if type(e) is bw.ShapeRef:
        #         e.shape.attach_to_plane(surf, face_edges_yz[j][1],face_edges_yz[j][0])
        #     else:
        #         e.attach_to_plane(surf, *face_edges_yz[j])

        e1.attach_to_plane(surf, (0, 0), (0, 1) )
        e2.attach_to_plane(surf, (0, 1), (1, 1) )
        e3.attach_to_plane(surf, (1, 1), (1, 0) )
        e4.attach_to_plane(surf, (1, 0), (0, 0) )

        for j, e in enumerate(face_edges[i]):
            if type(e) is bw.ShapeRef:
                e.shape.attach_to_plane(surf, face_edges_yz[i][j][1],face_edges_yz[i][j][0])
            else:
                e.attach_to_plane(surf, *face_edges_yz[i][j])

        faces.append(bw.Face([bw.Wire([e1, e2, e3, e4]), bw.Wire(face_edges[i])], surface=surf))
        #f1 = bw.Face(bw.Wire(face_edges).m())
        #f1 = bw.Face([e1, e2, e3, e4], surface=surf)




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

    f3 = bw.Face([e1, e10, e5.m(), e9.m()])
    f4 = bw.Face([e2, e11, e6.m(), e10.m()])
    f5 = bw.Face([e3, e12, e7.m(), e11.m()])
    f6 = bw.Face([e4, e9, e8.m(), e12.m()])

    for i in [2]:#range(6):
        #surf, vtxs_uv = bw.Approx.plane([(box[1][0], 0, 0), (box[1][0], 1, 0), (box[1][0], 0, 1)])
        #surf, vtxs_uv = bw.Approx.plane([planes[i][0], planes[i][0] + planes[i][1], planes[i][0] + planes[i][2]])
        surf, vtxs_uv = bw.Approx.plane([v5.point, v5.point + gen_vecs[0], v5.point + gen_vecs[2]])
        print(vtxs_uv)
        # e1.attach_to_plane(surf, (box[0][1], box[0][2]), (box[0][1], box[1][2]) )
        # e2.attach_to_plane(surf, (box[0][1], box[1][2]), (box[1][1], box[1][2]) )
        # e3.attach_to_plane(surf, (box[1][1], box[1][2]), (box[1][1], box[0][2]) )
        # e4.attach_to_plane(surf, (box[1][1], box[0][2]), (box[0][1], box[0][2]) )
        #
        # for j, e in enumerate(face_edges[i]):
        #     if type(e) is bw.ShapeRef:
        #         e.shape.attach_to_plane(surf, face_edges_yz[j][1],face_edges_yz[j][0])
        #     else:
        #         e.attach_to_plane(surf, *face_edges_yz[j])

        e1.attach_to_plane(surf, (1, 0), (1, 1) )
        e10.attach_to_plane(surf, (1, 1), (0, 1) )
        # e5.m().attach_to_plane(surf, (1, 1), (1, 0) )
        # e9.m().attach_to_plane(surf, (1, 0), (0, 0) )
        e5.attach_to_plane(surf, (0, 0), (0, 1) )
        e9.attach_to_plane(surf, (1, 0), (0, 0) )

        for j, e in enumerate(face_edges[i]):
            if type(e) is bw.ShapeRef:
                e.shape.attach_to_plane(surf, face_edges_xz[i][j][1],face_edges_xz[i][j][0])
            else:
                e.attach_to_plane(surf, *face_edges_xz[i][j])

        faces.append(bw.Face([bw.Wire([e1, e10, e5.m(), e9.m()]), bw.Wire(face_edges[i])], surface=surf))
        #f1 = bw.Face(bw.Wire(face_edges).m())
        #f1 = bw.Face([e1, e2, e3, e4], surface=surf)


    for i in [5]:#range(6):
        #surf, vtxs_uv = bw.Approx.plane([(box[1][0], 0, 0), (box[1][0], 1, 0), (box[1][0], 0, 1)])
        #surf, vtxs_uv = bw.Approx.plane([planes[i][0], planes[i][0] + planes[i][1], planes[i][0] + planes[i][2]])
        surf, vtxs_uv = bw.Approx.plane([v8.point, v8.point + gen_vecs[0], v8.point + gen_vecs[2]])
        print(vtxs_uv)
        # e1.attach_to_plane(surf, (box[0][1], box[0][2]), (box[0][1], box[1][2]) )
        # e2.attach_to_plane(surf, (box[0][1], box[1][2]), (box[1][1], box[1][2]) )
        # e3.attach_to_plane(surf, (box[1][1], box[1][2]), (box[1][1], box[0][2]) )
        # e4.attach_to_plane(surf, (box[1][1], box[0][2]), (box[0][1], box[0][2]) )
        #
        # for j, e in enumerate(face_edges[i]):
        #     if type(e) is bw.ShapeRef:
        #         e.shape.attach_to_plane(surf, face_edges_yz[j][1],face_edges_yz[j][0])
        #     else:
        #         e.attach_to_plane(surf, *face_edges_yz[j])

        e3.attach_to_plane(surf, (1, 1), (1, 0) )
        e12.attach_to_plane(surf, (1, 0), (0, 0) )
        e7.attach_to_plane(surf, (0, 1), (0, 0) )
        e11.attach_to_plane(surf, (1, 1), (0, 1) )

        for j, e in enumerate(face_edges[i]):
            if type(e) is bw.ShapeRef:
                e.shape.attach_to_plane(surf, face_edges_xz[i][j][1],face_edges_xz[i][j][0])
            else:
                e.attach_to_plane(surf, face_edges_xz[i][j][0],face_edges_xz[i][j][1])

        faces.append(bw.Face([bw.Wire([e3, e12, e7.m(), e11.m()]), bw.Wire([f for f in face_edges[i]])], surface=surf))
        #faces.append(bw.Face([bw.Wire([e11, e7, e12.m(), e3.m()]), bw.Wire(reversed(face_edges[i]))], surface=surf))
        #faces.append(bw.Face([bw.Wire([e11, e7, e12.m(), e3.m()]), bw.Wire([f.m() for f in reversed(face_edges[i])])], surface=surf))
        #f1 = bw.Face(bw.Wire(face_edges).m())
        #f1 = bw.Face([e1, e2, e3, e4], surface=surf)


    for i in [1]:#range(6):
        #surf, vtxs_uv = bw.Approx.plane([(box[1][0], 0, 0), (box[1][0], 1, 0), (box[1][0], 0, 1)])
        #surf, vtxs_uv = bw.Approx.plane([planes[i][0], planes[i][0] + planes[i][1], planes[i][0] + planes[i][2]])
        surf, vtxs_uv = bw.Approx.plane([v5.point, v5.point + gen_vecs[1], v5.point + gen_vecs[2]])
        print(vtxs_uv)
        # e1.attach_to_plane(surf, (box[0][1], box[0][2]), (box[0][1], box[1][2]) )
        # e2.attach_to_plane(surf, (box[0][1], box[1][2]), (box[1][1], box[1][2]) )
        # e3.attach_to_plane(surf, (box[1][1], box[1][2]), (box[1][1], box[0][2]) )
        # e4.attach_to_plane(surf, (box[1][1], box[0][2]), (box[0][1], box[0][2]) )
        #
        # for j, e in enumerate(face_edges[i]):
        #     if type(e) is bw.ShapeRef:
        #         e.shape.attach_to_plane(surf, face_edges_yz[j][1],face_edges_yz[j][0])
        #     else:
        #         e.attach_to_plane(surf, *face_edges_yz[j])

        e5.attach_to_plane(surf, (0, 0), (0, 1) )
        e6.attach_to_plane(surf, (0, 1), (1, 1) )
        e7.attach_to_plane(surf, (1, 1), (1, 0) )
        e8.attach_to_plane(surf, (1, 0), (0, 0) )

        for j, e in enumerate(face_edges[i]):
            if type(e) is bw.ShapeRef:
                e.shape.attach_to_plane(surf, face_edges_yz[i][j][1],face_edges_yz[i][j][0])
            else:
                e.attach_to_plane(surf, *face_edges_yz[i][j])

        faces.append(bw.Face([bw.Wire([e5, e6, e7, e8]), bw.Wire(face_edges[i])], surface=surf))
        #f1 = bw.Face(bw.Wire(face_edges).m())
        #f1 = bw.Face([e1, e2, e3, e4], surface=surf)


    shell = bw.Shell(bw_faces + faces + [f4, f6])
    #shell = bw.Shell(faces + [f2, f4, f6])
    #shell = bw.Shell([f1])

    s1 = bw.Solid([shell])

    c1 = bw.Compound([s1])

    with open("inv_mesh_tmp.brep", "w") as f:
        bw.write_model(f, c1, bw.Location())
        # bw.write_model(sys.stdout, c1, cloc)
    #print(c1)
    #print([vi.plane_pos for vi in vert_info.values()])
