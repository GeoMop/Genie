import numpy as np


def cut_tool_to_gen_vecs(mesh_cut_tool_param, only_inv = False, margin=False):
    mc = mesh_cut_tool_param

    z_min, z_max = sorted([mc.z_min, mc.z_max])

    base_point = np.array([mc.origin_x, mc.origin_y, z_min])

    v1 = np.array([mc.gen_vec1_x, mc.gen_vec1_y, 0.0])
    v2 = np.array([mc.gen_vec2_x, mc.gen_vec2_y, 0.0])
    if v1[0] * v2[1] - v1[1] * v2[0] < 0:
        v1, v2 = v2, v1
    gen_vecs = [v1, v2, np.array([0.0, 0.0, z_max - z_min])]

    if not only_inv:
        base_point -= sum(gen_vecs) * ((mc.no_inv_factor - 1) * 0.5)
        gen_vecs = [v * mc.no_inv_factor for v in gen_vecs]

    if margin:
        # m = mc.margin
        # gn = [v / np.linalg.norm(v) for v in gen_vecs]
        # base_point -= sum(gn) * m
        # gen_vecs = [v + n * (m * 2) for v, n in zip(gen_vecs, gn)]
        base_point -= sum(gen_vecs) / 2
        gen_vecs = [v * 2 for v in gen_vecs]

    return base_point, gen_vecs


def inv_tr(gen_vecs):
    a = np.array(gen_vecs).T
    return np.linalg.inv(a)


def tr_to_local(base_point, inv_tr_mat, point):
    return inv_tr_mat @ (point - base_point)


def cut_ascii(in_file, out_file, mesh_cut_tool_param, project_conf):
    base_point, gen_vecs = cut_tool_to_gen_vecs(mesh_cut_tool_param, margin=True)
    base_point -= np.array([project_conf.point_cloud_origin_x,
                            project_conf.point_cloud_origin_y,
                            project_conf.point_cloud_origin_z])
    vs = []
    vs.append(base_point)
    vs.append(base_point + gen_vecs[0])
    vs.append(base_point + gen_vecs[0] + gen_vecs[1])
    vs.append(base_point + gen_vecs[1])
    vs.append(base_point + gen_vecs[2])
    vs.append(base_point + gen_vecs[2] + gen_vecs[0])
    vs.append(base_point + gen_vecs[2] + gen_vecs[0] + gen_vecs[1])
    vs.append(base_point + gen_vecs[2] + gen_vecs[1])

    x_min = x_max = vs[0][0]
    y_min = y_max = vs[0][1]
    z_min = z_max = vs[0][2]
    for v in vs[1:]:
        if v[0] < x_min:
            x_min = v[0]
        if v[0] > x_max:
            x_max = v[0]
        if v[1] < y_min:
            y_min = v[1]
        if v[1] > y_max:
            y_max = v[1]
        if v[2] < z_min:
            z_min = v[2]
        if v[2] > z_max:
            z_max = v[2]

    inv_tr_mat = inv_tr(gen_vecs)

    b0 = base_point[0]
    b1 = base_point[1]
    b2 = base_point[2]

    m00 = inv_tr_mat[0][0]
    m01 = inv_tr_mat[0][1]
    m02 = inv_tr_mat[0][2]
    m10 = inv_tr_mat[1][0]
    m11 = inv_tr_mat[1][1]
    m12 = inv_tr_mat[1][2]
    m20 = inv_tr_mat[2][0]
    m21 = inv_tr_mat[2][1]
    m22 = inv_tr_mat[2][2]

    with open(in_file) as fd_in:
        with open(out_file, "w") as fd_out:
            points_count = 0
            points_count_show = 1000000
            for line in fd_in:
                s = line.split()
                if len(s) < 3:
                    continue

                points_count += 1
                if points_count % points_count_show == 0:
                    print("{} points read.".format(points_count))

                x = float(s[0])
                if (x < x_min) or (x > x_max):
                    continue
                y = float(s[1])
                if (y < y_min) or (y > y_max):
                    continue
                z = float(s[2])
                if (z < z_min) or (z > z_max):
                    continue

                xb = x - b0
                yb = y - b1
                zb = z - b2
                l0 = m00 * xb + m01 * yb + m02 * zb
                if (l0 < 0) or (l0 > 1):
                    continue
                l1 = m10 * xb + m11 * yb + m12 * zb
                if (l1 < 0) or (l1 > 1):
                    continue
                l2 = m20 * xb + m21 * yb + m22 * zb
                if (l2 < 0) or (l2 > 1):
                    continue

                out_line = s[0] + " " + s[1] + " " + s[2]
                fd_out.write(out_line + "\n")

            print("{} points read.".format(points_count))


def cut_bin(in_file, out_file, mesh_cut_tool_param):
    import time
    t = time.time()
    xxx = np.float32(np.loadtxt(fd_in))
    #a=np.load("np_bin.npy")
    print("elapsed time: {:0.3f} s".format(time.time() - t))
    t = time.time()
    #np.savetxt('test.out', xxx, fmt="%3.2f")
    np.save("np_bin", xxx, allow_pickle=False, fix_imports=False)
    print("elapsed time: {:0.3f} s".format(time.time() - t))
