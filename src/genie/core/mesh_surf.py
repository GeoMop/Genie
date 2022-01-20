from bgem.bspline import brep_writer as bw
from bgem.bspline import bspline_approx as bs_approx
import bgem.bspline.bspline as bs
from .cut_point_cloud import cut_tool_to_gen_vecs, inv_tr

import numpy as np


def gen(cloud_file, out_brep_file, mesh_cut_tool_param):
    surf_approx = bs_approx.SurfaceApprox.approx_from_file(cloud_file)

    quad = surf_approx.compute_default_quad()
    nuv = surf_approx.compute_default_nuv()
    nuv = nuv / 5
    surface = surf_approx.compute_approximation()
    #surface = surf_approx.compute_approximation(quad=quad, nuv=nuv)
    surface_3d = surface.make_full_surface()
    bw_surface = bw.surface_from_bs(surface_3d)

    a = bw_surface._bs_surface.eval(0, 0)
    b = bw_surface._bs_surface.eval(1, 0)
    c = bw_surface._bs_surface.eval(0, 1)

    base_point, gen_vecs = cut_tool_to_gen_vecs(mesh_cut_tool_param)

    a[2] = 0
    b[2] = 0
    c[2] = 0

    ab = b - a
    ac = c - a
    tr = np.array([ab, ac, [0, 0, 1]]).T
    inv_tr = np.linalg.inv(tr)

    v1 = bw.Vertex(base_point + gen_vecs[0])
    v2 = bw.Vertex(base_point + gen_vecs[2] + gen_vecs[0])
    v3 = bw.Vertex(base_point + gen_vecs[2] + gen_vecs[1] + gen_vecs[0])
    v4 = bw.Vertex(base_point + gen_vecs[1] + gen_vecs[0])

    v5 = bw.Vertex(base_point)
    v6 = bw.Vertex(base_point + gen_vecs[2])
    v7 = bw.Vertex(base_point + gen_vecs[2] + gen_vecs[1])
    v8 = bw.Vertex(base_point + gen_vecs[1])

    v2l = inv_tr @ (v2.point - a)
    v3l = inv_tr @ (v3.point - a)
    v6l = inv_tr @ (v6.point - a)
    v7l = inv_tr @ (v7.point - a)

    try:
        v2s = bw_surface._bs_surface.eval(v2l[0], v2l[1])
        v3s = bw_surface._bs_surface.eval(v3l[0], v3l[1])
        v6s = bw_surface._bs_surface.eval(v6l[0], v6l[1])
        v7s = bw_surface._bs_surface.eval(v7l[0], v7l[1])
    except IndexError:
        print("Error: Mesh cut area must be inside surface point cloud.")
        return False, bw_surface

    v2h = v2s[2] - base_point[2]
    v3h = v3s[2] - base_point[2]
    v6h = v6s[2] - base_point[2]
    v7h = v7s[2] - base_point[2]

    v2.point[2] = v2s[2]
    v3.point[2] = v3s[2]
    v6.point[2] = v6s[2]
    v7.point[2] = v7s[2]

    e1 = bw.Edge([v1, v2])
    e2 = bw.Edge([v2, v3])
    e3 = bw.Edge([v3, v4])
    e4 = bw.Edge([v4, v1])


    e5 = bw.Edge([v5, v6])
    e6 = bw.Edge([v6, v7])
    e7 = bw.Edge([v7, v8])
    e8 = bw.Edge([v8, v5])

    e9 = bw.Edge([v1, v5])
    e10 = bw.Edge([v2, v6])
    e11 = bw.Edge([v3, v7])
    e12 = bw.Edge([v4, v8])


    faces = []

    # top
    e2.attach_to_surface(bw_surface, (v2l[0], v2l[1]), (v3l[0], v3l[1]))
    e11.attach_to_surface(bw_surface, (v3l[0], v3l[1]), (v7l[0], v7l[1]))
    e6.attach_to_surface(bw_surface, (v6l[0], v6l[1]), (v7l[0], v7l[1]))
    e10.attach_to_surface(bw_surface, (v2l[0], v2l[1]), (v6l[0], v6l[1]))

    faces.append(bw.Face([bw.Wire([e2, e11, e6, e10])], surface=bw_surface))

    # bottom
    surf, vtxs_uv = bw.Approx.plane([v5.point, v5.point + gen_vecs[0], v5.point + gen_vecs[1]])

    e4.attach_to_surface(surf, (1, 1), (1, 0))
    e9.attach_to_surface(surf, (1, 0), (0, 0))
    e8.attach_to_surface(surf, (0, 1), (0, 0))
    e12.attach_to_surface(surf, (1, 1), (0, 1))

    faces.append(bw.Face([bw.Wire([e4, e9, e8, e12])], surface=surf))


    def get_curves(v0, v1):
        n_points = 100
        u_points = np.linspace(v0[0], v1[0], n_points)
        v_points = np.linspace(v0[1], v1[1], n_points)
        uv_points = np.stack((u_points, v_points), axis=1)
        xyz_points = bw_surface._bs_surface.eval_array(uv_points)
        curve_xyz = bs_approx.curve_from_grid(xyz_points)

        poles_z = curve_xyz.poles[:, 2].copy()
        x_diff, y_diff, z_diff = np.abs(xyz_points[-1] - xyz_points[0])
        if x_diff > y_diff:
            axis = 0
        else:
            axis = 1
        poles_t = curve_xyz.poles[:, axis].copy()
        poles_t -= xyz_points[0][axis]
        poles_t /= (xyz_points[-1][axis] - xyz_points[0][axis])
        poles_z -= base_point[2]
        poles_tz = np.stack((poles_t, poles_z), axis=1)
        curve_tz = bs.Curve(curve_xyz.basis, poles_tz)

        return bw.curve_from_bs(curve_tz), bw.curve_from_bs(curve_xyz)


    surf, vtxs_uv = bw.Approx.plane([v1.point, v1.point + gen_vecs[1], v1.point + [0, 0, 1]])
    assert vtxs_uv == [(0, 0), (1, 0), (0, 1)]

    e1.attach_to_surface(surf, (0, 0), (0, v2h))
    curve_tz, curve_xyz = get_curves(v2l, v3l)
    e2.attach_to_2d_curve((0.0, 1.0), curve_tz, surf)
    e2.attach_to_3d_curve((0.0, 1.0), curve_xyz)
    e3.attach_to_surface(surf, (1, v3h), (1, 0))
    e4.attach_to_surface(surf, (1, 0), (0, 0))

    faces.append(bw.Face([bw.Wire([e1, e2, e3, e4])], surface=surf))


    surf, vtxs_uv = bw.Approx.plane([v5.point + gen_vecs[0], v5.point, v5.point + gen_vecs[0] + [0, 0, 1]])
    assert vtxs_uv == [(0, 0), (1, 0), (0, 1)]

    e1.attach_to_surface(surf, (0, 0), (0, v2h))
    curve_tz, curve_xyz = get_curves(v2l, v6l)
    e10.attach_to_2d_curve((0.0, 1.0), curve_tz, surf)
    e10.attach_to_3d_curve((0.0, 1.0), curve_xyz)
    e5.attach_to_surface(surf, (1, 0), (1, v6h))
    e9.attach_to_surface(surf, (0, 0), (1, 0))

    faces.append(bw.Face([bw.Wire([e1, e10, e5, e9])], surface=surf))


    surf, vtxs_uv = bw.Approx.plane([v8.point + gen_vecs[0], v8.point, v8.point + gen_vecs[0] + [0, 0, 1]])
    assert vtxs_uv == [(0, 0), (1, 0), (0, 1)]

    e3.attach_to_surface(surf, (0, v3h), (0, 0))
    e12.attach_to_surface(surf, (0, 0), (1, 0))
    e7.attach_to_surface(surf, (1, v7h), (1, 0))
    curve_tz, curve_xyz = get_curves(v3l, v7l)
    e11.attach_to_2d_curve((0.0, 1.0), curve_tz, surf)
    e11.attach_to_3d_curve((0.0, 1.0), curve_xyz)

    faces.append(bw.Face([bw.Wire([e3, e12, e7, e11])], surface=surf))


    surf, vtxs_uv = bw.Approx.plane([v5.point, v5.point + gen_vecs[1], v5.point + [0, 0, 1]])
    assert vtxs_uv == [(0, 0), (1, 0), (0, 1)]

    e5.attach_to_surface(surf, (0, 0), (0, v6h))
    curve_tz, curve_xyz = get_curves(v6l, v7l)
    e6.attach_to_2d_curve((0.0, 1.0), curve_tz, surf)
    e6.attach_to_3d_curve((0.0, 1.0), curve_xyz)
    e7.attach_to_surface(surf, (1, v7h), (1, 0))
    e8.attach_to_surface(surf, (1, 0), (0, 0))

    faces.append(bw.Face([bw.Wire([e5, e6, e7, e8])], surface=surf))


    shell = bw.Shell(faces)

    s1 = bw.Solid([shell])

    c1 = bw.Compound([s1])

    with open(out_brep_file, "w") as f:
        bw.write_model(f, c1)

    return True, bw_surface
