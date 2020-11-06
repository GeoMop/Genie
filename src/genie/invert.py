"""
Script for run inversion in separate process.
"""

import json
import psutil
import sys
import os
import subprocess
import time
import math

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from genie.core import snap_electrodes
from genie.core.config import InversionConfig, ProjectConfig
from genie.core import mesh_gen2, mesh_gen3, mesh_surf, meshlab_script_gen
from genie.core import cut_point_cloud
from genie.core.data_types import MeasurementsInfo, MeshFrom
from genie.core.global_const import GenieMethod
from bgem.gmsh.gmsh_io import GmshIO

import numpy as np
#import pybert as pb
import pygimli as pg
from pygimli.physics.traveltime import Refraction


def main():
    # read config file
    conf_file = "inv.conf"
    with open(conf_file, "r") as fd:
        conf = json.load(fd)
    inversion_conf = InversionConfig.deserialize(conf)

    prj_conf_file = "../../genie.prj"
    with open(prj_conf_file, "r") as fd:
        prj_conf = json.load(fd)
    project_conf = ProjectConfig.deserialize(prj_conf)

    if project_conf.method == GenieMethod.ERT:
        inv_ert(inversion_conf, project_conf)
    else:
        inv_st(inversion_conf, project_conf)


def inv_ert(inversion_conf, project_conf):
    inv_par = inversion_conf.inversion_param
    cut_par = inversion_conf.mesh_cut_tool_param

    remove_old_files()

    if not prepare(cut_par, inv_par, project_conf):
        return
    #return

    # snap electrodes
    print()
    print_headline("Snapping electrodes")
    snap_electrodes.main(inv_par, project_conf, max_dist=inv_par.snapDistance)

    #ball_mesh("inv_mesh.msh", "inv_mesh2.msh", [-622342, -1128822, 22], 5.0)
    #return

    print()
    print_headline("Inversion")

    # res = pb.Resistivity("input.dat")
    # res.invert()
    # np.savetxt('resistivity.vector', res.resistivity)
    # return

    # load data file
    data = pg.DataContainerERT("input_snapped.dat", removeInvalid=False)
    #data = pg.DataContainerERT("ldp2.dat")
    #print(data.size())
    #print(data("a"))
    #print(data.sensorIdx())
    #return

    # mark all data valid
    #data.markValid(data('rhoa') > 0)
    #data.markValid(data('rhoa') <= 0)
    #data.markValid(data('u') > 0)

    # k, rhoa
    #inv_par.k_ones = True
    if inv_par.k_ones:
        data.set("k", np.ones(data.size()))
    else:
        data.set("k", pg.geometricFactors(data))
    #data.set("err", pb.Resistivity.estimateError(data, absoluteUError=0.0001, relativeError=0.03))
    #data.set("k", np.ones(data.size()))
    #data.set("k", pg.geometricFactors(data))
    data.set("rhoa", data("u") / data("i") * data("k"))
    tolerance = 1e-12
    #data.markValid(np.abs(data('rhoa')) > tolerance)
    data.markValid(data('rhoa') > tolerance)
    data.markInvalid(data('rhoa') <= tolerance) # udelat poradne

    # remove invalid data
    oldsize = data.size()
    data.removeInvalid()
    newsize = data.size()
    if newsize < oldsize:
        print('Removed ' + str(oldsize - newsize) + ' values.')
    if not data.allNonZero('rhoa'):
        print("No or partial rhoa values.")
        return

    # check, compute error
    # if data.allNonZero('err'):
    #     error = data('err')
    # else:
    #     print("estimate data error")
    #     error = inv_par.relativeError + inv_par.absoluteError / data('rhoa')
    error = data('err')
    min_err = 0.0005
    for i in range(data.size()):
        if error[i] < min_err:
            error[i] = min_err

    # create FOP
    fop = pg.DCSRMultiElectrodeModelling(verbose=inv_par.verbose)
    fop.setThreadCount(psutil.cpu_count(logical=False))
    fop.setData(data)

    # create Inv
    inv = pg.RInversion(verbose=inv_par.verbose, dosave=False)
    # variables tD, tM are needed to prevent destruct objects
    tM = pg.RTransLogLU(inv_par.minModel, inv_par.maxModel)
    if inv_par.data_log:
        tD = pg.RTransLog()
        inv.setTransData(tD)
    inv.setTransModel(tM)
    inv.setForwardOperator(fop)

    # mesh
    mesh_file = "inv_mesh.msh"
    #mesh_file = inv_par.meshFile
    if mesh_file == "":
        depth = inv_par.depth
        if depth is None:
            depth = pg.DCParaDepth(data)

        poly = pg.meshtools.createParaMeshPLC(
            data.sensorPositions(), paraDepth=depth, paraDX=inv_par.paraDX,
            paraMaxCellSize=inv_par.maxCellArea, paraBoundary=2, boundary=2)

        if inv_par.verbose:
            print("creating mesh...")
        mesh = pg.meshtools.createMesh(poly, quality=inv_par.quality, smooth=(1, 10))
    else:
        mesh = pg.Mesh(pg.load(mesh_file))

    mesh.createNeighbourInfos()

    if inv_par.verbose:
        print(mesh)

    sys.stdout.flush()  # flush before multithreading
    fop.setMesh(mesh)
    fop.regionManager().setConstraintType(1)

    # print(fop.regionManager().regionCount())
    # print(fop.regionManager().paraDomain().cellMarkers())
    # pg.show(mesh, data=mesh.cellMarkers())
    # print(fop.regionManager().region(1).cellMarkers())
    # return

    # we have only one region
    # if not inv_par.omitBackground:
    #     if fop.regionManager().regionCount() > 1:
    #         fop.regionManager().region(1).setBackground(True)

    if mesh_file == "":
        fop.createRefinedForwardMesh(True, False)
    else:
        fop.createRefinedForwardMesh(inv_par.refineMesh, inv_par.refineP2)

    paraDomain = fop.regionManager().paraDomain()
    inv.setForwardOperator(fop)  # necessary?

    # in_ball = find_markers_in_ball(paraDomain, [-622342, -1128822, 22], 5.0)
    # print(pg.median(data('rhoa')))
    # pc = fop.regionManager().parameterCount()
    # x = pg.RVector(pc, 10000.0)
    # for i, m in enumerate(paraDomain.cellMarkers()):
    #     if m in in_ball:
    #         x[i] = 1000.0
    # resp = fop.response(x)
    # print(resp)
    #return

    # inversion parameters
    inv.setData(data('rhoa'))
    #inv.setData(resp)
    inv.setRelativeError(error)
    #inv.setRelativeError(pg.RVector(data.size(), 0.03))
    fop.regionManager().setZWeight(inv_par.zWeight)
    inv.setLambda(inv_par.lam)
    if inv_par.optimizeLambda:
        inv.setOptimizeLambda(True)
    inv.setMaxIter(inv_par.maxIter)
    inv.setRobustData(inv_par.robustData)
    inv.setBlockyModel(inv_par.blockyModel)
    inv.setRecalcJacobian(inv_par.recalcJacobian)

    pc = fop.regionManager().parameterCount()
    if inv_par.k_ones:
        # hack of gimli hack
        v = pg.RVector(pg.RVector(pc, pg.median(data('rhoa') * pg.geometricFactors(data))))
        v[0] += tolerance * 2
        startModel = v
    else:
        startModel = pg.RVector(pc, pg.median(data('rhoa')))
    #startModel = pg.RVector(pc, 2000.0)

    inv.setModel(startModel)

    # Run the inversion
    sys.stdout.flush()  # flush before multithreading
    model = inv.run()
    resistivity = model(paraDomain.cellMarkers())
    np.savetxt('resistivity.vector', resistivity)
    paraDomain.addExportData('Resistivity', resistivity)
    #paraDomain.addExportData('Resistivity (log10)', np.log10(resistivity))
    #paraDomain.addExportData('Coverage', coverageDC(fop, inv, paraDomain))
    paraDomain.exportVTK('resistivity')

    # measurements on model
    print()
    print_headline("Measurements on model")
    with open("measurements_info.json") as fd:
        meas_info = MeasurementsInfo.deserialize(json.load(fd))

    resp = fop.response(resistivity)
    # hack of gimli hack
    v = pg.RVector(startModel)
    v[0] += tolerance * 2
    resp_start = fop.response(v)

    map = {}
    map_start = {}
    map_appres_gimli = {}
    for i in range(data.size()):
        map[(data("a")[i], data("b")[i], data("m")[i], data("n")[i])] = resp[i]
        map_start[(data("a")[i], data("b")[i], data("m")[i], data("n")[i])] = resp_start[i]
        map_appres_gimli[(data("a")[i], data("b")[i], data("m")[i], data("n")[i])] = data('rhoa')[i]

    with open("measurements_model.txt", "w") as fd:
        fd.write("meas_number ca  cb  pa  pb  I[A]      V[V]     AppRes[Ohmm] std    AppResGimli[Ohmm] AppResModel[Ohmm]   ratio AppResStartModel[Ohmm] start_ratio\n")
        fd.write("-------------------------------------------------------------------------------------------------------------------------------------------------\n")
        for item in meas_info.items:
            k = (item.inv_ca, item.inv_cb, item.inv_pa, item.inv_pb)
            if k in map:
                m_on_m = "{:17.2f} {:17.2f} {:7.2f} {:22.2f}     {:7.2f}".format(map_appres_gimli[k], map[k], map[k]/map_appres_gimli[k], map_start[k], map_start[k]/map_appres_gimli[k])
            else:
                m_on_m = "         not used"

            fd.write("{:11} {:3} {:3} {:3} {:3} {:8.6f} {:9.6f} {:12.2f} {:6.4f} {}\n".format(item.measurement_number, item.ca, item.cb, item.pa, item.pb, item.I, item.V, item.AppRes, item.std, m_on_m))

    print()
    print_headline("Saving p3d")
    t = time.time()
    save_p3d(paraDomain, model.array(), cut_par, 1.0, "resistivity")
    print("save_p3d elapsed time: {:0.3f} s".format(time.time() - t))

    print()
    print("All done.")


def inv_st(inversion_conf, project_conf):
    inv_par = inversion_conf.inversion_param
    cut_par = inversion_conf.mesh_cut_tool_param

    remove_old_files()

    if not prepare(cut_par, inv_par, project_conf):
        return
    #return

    # snap electrodes
    print()
    print_headline("Snapping electrodes")
    snap_electrodes.main(inv_par, project_conf, max_dist=inv_par.snapDistance)

    print()
    print_headline("Inversion")

    # load data file
    data = pg.DataContainer("input_snapped.dat", sensorTokens='s g', removeInvalid=False)

    # remove invalid data
    oldsize = data.size()
    data.removeInvalid()
    newsize = data.size()
    if newsize < oldsize:
        print('Removed ' + str(oldsize - newsize) + ' values.')

    # create FOP
    fop = pg.TravelTimeDijkstraModelling(verbose=inv_par.verbose)
    fop.setThreadCount(psutil.cpu_count(logical=False))
    fop.setData(data)

    # create Inv
    inv = pg.RInversion(verbose=inv_par.verbose, dosave=False)
    # variables tD, tM are needed to prevent destruct objects
    tM = pg.RTransLogLU(inv_par.minModel, inv_par.maxModel)
    tD = pg.RTrans()
    inv.setTransData(tD)
    inv.setTransModel(tM)
    inv.setForwardOperator(fop)

    # mesh
    mesh_file = "inv_mesh.msh"
    if mesh_file == "":
        depth = inv_par.depth
        if depth is None:
            depth = pg.DCParaDepth(data)

        poly = pg.meshtools.createParaMeshPLC(
            data.sensorPositions(), paraDepth=depth, paraDX=inv_par.paraDX,
            paraMaxCellSize=inv_par.maxCellArea, paraBoundary=2, boundary=2)

        if inv_par.verbose:
            print("creating mesh...")
        mesh = pg.meshtools.createMesh(poly, quality=inv_par.quality, smooth=(1, 10))
    else:
        mesh = pg.Mesh(pg.load(mesh_file))

    mesh.createNeighbourInfos()

    if inv_par.verbose:
        print(mesh)

    sys.stdout.flush()  # flush before multithreading
    fop.setMesh(mesh)
    fop.regionManager().setConstraintType(1)

    if mesh_file == "":
        fop.createRefinedForwardMesh(True, False)
    else:
        fop.createRefinedForwardMesh(inv_par.refineMesh, inv_par.refineP2)

    paraDomain = fop.regionManager().paraDomain()
    inv.setForwardOperator(fop)  # necessary?

    # inversion parameters
    inv.setData(data('t'))
    error = Refraction.estimateError(data, absoluteError=0.001, relativeError=0.001)
    inv.setAbsoluteError(error)
    #inv.setRelativeError(pg.RVector(data.size(), 0.03))
    fop.regionManager().setZWeight(inv_par.zWeight)
    inv.setLambda(inv_par.lam)
    if inv_par.optimizeLambda:
        inv.setOptimizeLambda(True)
    inv.setMaxIter(inv_par.maxIter)
    inv.setRobustData(inv_par.robustData)
    inv.setBlockyModel(inv_par.blockyModel)
    inv.setRecalcJacobian(inv_par.recalcJacobian)

    startModel = fop.createDefaultStartModel()
    inv.setModel(startModel)

    # Run the inversion
    sys.stdout.flush()  # flush before multithreading
    model = inv.run()
    velocity = 1.0 / model(paraDomain.cellMarkers())
    np.savetxt('velocity.vector', velocity)
    paraDomain.addExportData('Velocity', velocity)
    paraDomain.exportVTK('velocity')

    print()
    print_headline("Saving p3d")
    t = time.time()
    save_p3d(paraDomain, 1.0 / model.array(), cut_par, 1.0, "velocity")
    print("save_p3d elapsed time: {:0.3f} s".format(time.time() - t))

    print()
    print("All done.")


def coverageDC(fop, inv, paraDomain):
    """
    Return coverage vector considering the logarithmic transformation.
    """
    covTrans = pg.coverageDCtrans(fop.jacobian(),
                                  1.0/inv.response(),
                                  1.0/inv.model())
    return np.log10(covTrans / paraDomain.cellSizes())


def save_csv(paraDomain, model, file_name):
    xmin = paraDomain.xmin()
    xmax = paraDomain.xmax()
    ymin = paraDomain.ymin()
    ymax = paraDomain.ymax()
    zmin = paraDomain.zmin()
    zmax = paraDomain.zmax()

    with open(file_name, "w") as fd:
        fd.write('"x","y","z","resistivity"\n')

        m = model.array()
        for k in range(10):
            z = zmin + (zmax - zmin) / 10 * k
            for j in range(10):
                y = ymin + (ymax - ymin) / 10 * j
                for i in range(10):
                    x = xmin + (xmax - xmin) / 10 * i
                    cell = paraDomain.findCell(pg.RVector3(x, y, z))
                    if cell == None:
                        continue
                    r = m[cell.id()]
                    fd.write("{},{},{},{}\n".format(x, y, z, r))


def save_p3d(paraDomain, model_array, mesh_cut_tool_param, step, file_name):
    """Saves result as .p3d file."""
    base_point, gen_vecs = cut_point_cloud.cut_tool_to_gen_vecs(mesh_cut_tool_param)
    base_point[0] += - 622000
    base_point[1] += - 1128000

    x_nodes = math.floor(np.linalg.norm(gen_vecs[0]) / step) + 1
    y_nodes = math.floor(np.linalg.norm(gen_vecs[1]) / step) + 1
    z_nodes = math.floor(np.linalg.norm(gen_vecs[2]) / step) + 1

    x_knots = [1 / (x_nodes - 1) * i for i in range(x_nodes)]
    y_knots = [1 / (y_nodes - 1) * i for i in range(y_nodes)]
    z_knots = [1 / (z_nodes - 1) * i for i in range(z_nodes)]

    grid = [[[0.0] * x_nodes for _ in range(y_nodes)] for _ in range(z_nodes)]

    inv_tr_mat = cut_point_cloud.inv_tr(gen_vecs)
    for i in range(paraDomain.cellCount()):
        cell = paraDomain.cell(i)
        for j, n in enumerate(cell.nodes()):
            nl = cut_point_cloud.tr_to_local(base_point, inv_tr_mat, np.array([n[0], n[1], n[2]]))
            if j == 0:
                cxmin = cxmax = nl[0]
                cymin = cymax = nl[1]
                czmin = czmax = nl[2]
            else:
                if nl[0] < cxmin:
                    cxmin = nl[0]
                elif nl[0] > cxmax:
                    cxmax = nl[0]
                if nl[1] < cymin:
                    cymin = nl[1]
                elif nl[1] > cymax:
                    cymax = nl[1]
                if nl[2] < czmin:
                    czmin = nl[2]
                elif nl[2] > czmax:
                    czmax = nl[2]

        x_s = 0
        for i in range(1, len(x_knots)):
            if x_knots[i] < cxmin:
                x_s = i
            else:
                break
        x_e = len(x_knots)
        for i in reversed(range(0, len(x_knots))):
            if x_knots[i] > cxmax:
                x_e = i
            else:
                break
        y_s = 0
        for i in range(1, len(y_knots)):
            if y_knots[i] < cymin:
                y_s = i
            else:
                break
        y_e = len(y_knots)
        for i in reversed(range(0, len(y_knots))):
            if y_knots[i] > cymax:
                y_e = i
            else:
                break
        z_s = 0
        for i in range(1, len(z_knots)):
            if z_knots[i] < czmin:
                z_s = i
            else:
                break
        z_e = len(z_knots)
        for i in reversed(range(0, len(z_knots))):
            if z_knots[i] > czmax:
                z_e = i
            else:
                break

        r = model_array[cell.id()]

        shape = cell.shape()
        for k in range(z_s, z_e):
            for j in range(y_s, y_e):
                for i in range(x_s, x_e):
                    v = base_point + gen_vecs[0] * x_knots[i] + gen_vecs[1] * y_knots[j] + gen_vecs[2] * z_knots[k]
                    if shape.isInside(pg.RVector3(v)):
                        grid[k][j][i] = r

    def five_writer(fd):
        i = 0

        def write(s):
            nonlocal i
            i += 1
            if i > 1:
                fd.write(" ")
            fd.write(s)
            if i >= 5:
                fd.write("\n")
                i = 0

        def finalize():
            nonlocal i
            if i > 0:
                fd.write("\n")

        return write, finalize

    with open(file_name + ".p3d", "w") as fd_p3d:
        with open(file_name + ".q", "w") as fd_q:
            fd_p3d.write("{} {} {}\n".format(x_nodes, y_nodes, z_nodes))

            fd_q.write("{} {} {}\n".format(x_nodes, y_nodes, z_nodes))
            fd_q.write("{} {} {} {}\n".format(0.0, 0.0, 0.0, 0.0))

            x_list = []
            y_list = []
            z_list = []

            p3d_write, p3d_finalize = five_writer(fd_p3d)
            q_write, q_finalize = five_writer(fd_q)

            for rrr, zl in zip(grid, z_knots):
                for rr, yl in zip(rrr, y_knots):
                    for r, xl in zip(rr, x_knots):
                        q_write("{:.10g}".format(r))

                        v = base_point + gen_vecs[0] * xl + gen_vecs[1] * yl + gen_vecs[2] * zl
                        x_list.append(v[0])
                        y_list.append(v[1])
                        z_list.append(v[2])

            for v in x_list:
                p3d_write("{:.10g}".format(v))
            for v in y_list:
                p3d_write("{:.10g}".format(v))
            for v in z_list:
                p3d_write("{:.10g}".format(v))

            s = "{}".format(0.0)
            for _ in range(x_nodes * y_nodes * z_nodes * 4):
                q_write(s)

            p3d_finalize()
            q_finalize()


def modify_mesh(in_file, out_file):
    """Keeps only elements of dim 2 and 3. Sets physical id to 2."""
    el_type_to_dim = {15: 0, 1: 1, 2: 2, 4: 3}

    mesh = GmshIO(in_file)

    new_elements = {}
    for id, elm in mesh.elements.items():
        el_type, tags, nodes = elm
        dim = el_type_to_dim[el_type]
        if dim not in [2, 3]:
            continue
        physical_id = 2
        tags[0] = physical_id
        new_elements[id] = (el_type, tags, nodes)
    mesh.elements = new_elements

    with open(out_file, "w") as fd:
        mesh.write_ascii(fd)


def ball_mesh(in_file, out_file, pos, radius):
    """Sets physical id to 3 inside the ball."""
    pos = np.array(pos)

    el_type_to_dim = {15: 0, 1: 1, 2: 2, 4: 3}

    mesh = GmshIO(in_file)

    new_elements = {}
    for id, elm in mesh.elements.items():
        el_type, tags, nodes = elm
        dim = el_type_to_dim[el_type]
        if dim == 3:
            n_inside = 0
            for n in nodes:
                dis = np.linalg.norm(mesh.nodes[n] - pos)
                if dis <= radius:
                    n_inside += 1
            if n_inside >= 4:
                physical_id = 3
                tags[0] = physical_id
        new_elements[id] = (el_type, tags, nodes)
    mesh.elements = new_elements

    with open(out_file, "w") as fd:
        mesh.write_ascii(fd)


def find_markers_in_ball(paraDomain, pos, radius):
    pos = np.array(pos)

    in_ball = []
    for cm in paraDomain.cellMarkers():
        cell = paraDomain.findCellByMarker(cm)[0]
        n_inside = 0
        for n in cell.nodes():
            n_pos = np.array([n[0], n[1], n[2]])
            dis = np.linalg.norm(n_pos - pos)
            if dis <= radius:
                n_inside += 1
        if n_inside >= 4:
            in_ball.append(cm)

    return in_ball


def remove_old_files():
    files = [
        "point_cloud_cut.xyz",
        "gallery_mesh.ply",
        "gallery_mesh.msh",
        "input_snapped.dat",
        "inv_mesh_tmp.brep",
        "inv_mesh_tmp.msh",
        "inv_mesh.msh",
        "resistivity.vector",
        "resistivity.vtk",
        "resistivity.p3d",
        "resistivity.q",
        "velocity.vector",
        "velocity.vtk",
        "velocity.p3d",
        "velocity.q",
        "measurements_model.txt"
    ]

    for file_name in files:
        if os.path.isfile(file_name):
            os.remove(file_name)


def run_process(args):
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in p.stdout:
        print(line, end="")
    p.wait()


def print_headline(text):
    print(text)
    for i in range(len(text)):
        print("-", end="")
    print()


def prepare(mesh_cut_tool_param, inv_par, project_conf):
    #print("prepare !!!")

    gmsh_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "gmsh", "gmsh.exe")
    if not os.path.exists(gmsh_path):
        gmsh_path = "gmsh"

    if inv_par.meshFrom == MeshFrom.GALLERY_CLOUD:
        print_headline("Cutting point cloud")
        t = time.time()
        cut_point_cloud.cut_ascii(os.path.join("..", "..", "point_cloud.xyz"), "point_cloud_cut.xyz", mesh_cut_tool_param, project_conf)
        #cut_point_cloud.cut_ascii("point_cloud_cut_x.xyz", "point_cloud_cut.xyz", mesh_cut_tool_param)
        print("cutting elapsed time: {:0.3f} s".format(time.time() - t))
        #return

        # meshlab
        t = time.time()
        print()
        print_headline("Creating gallery mesh")
        #meshlabserver_path = '/home/radek/apps/meshlab'
        #os.environ['PATH'] = meshlabserver_path + os.pathsep + os.environ['PATH']
        meshlabserver_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "meshlab", "meshlabserver.exe")
        if not os.path.exists(meshlabserver_path):
            meshlabserver_path = "meshlabserver"
        meshlab_script_gen.gen("meshlab_script.mlx", inv_par.reconstructionDepth, inv_par.edgeLength)
        run_process([meshlabserver_path, "-i", "point_cloud_cut.xyz", "-o", "gallery_mesh.ply", "-m", "sa", "-s", "meshlab_script.mlx"])
        print("meshlab elapsed time: {:0.3f} s".format(time.time() - t))
        #return

        print()
        print_headline("Converting gallery mesh")
        run_process([gmsh_path, "-format", "msh2", "-save", "gallery_mesh.ply"])


    #return
    print()
    print_headline("Creating inversion mesh")
    if inv_par.meshFrom == MeshFrom.SURFACE_CLOUD:
        if not mesh_surf.gen(os.path.join("..", "..", "point_cloud.xyz"), "inv_mesh_tmp.brep", mesh_cut_tool_param):
            return False
    else:
        if inv_par.meshFrom == MeshFrom.GALLERY_CLOUD:
            gallery_mesh_file = "gallery_mesh.msh"
        elif inv_par.meshFrom == MeshFrom.GALLERY_MESH:
            gallery_mesh_file = "../../gallery_mesh.msh"
        #mesh_gen2.gen(mesh_cut_tool_param)
        if not mesh_gen3.gen(gallery_mesh_file, "inv_mesh_tmp.brep", mesh_cut_tool_param, inv_par, project_conf):
            print("Error in mesh generation")
            return False

    run_process([gmsh_path, "-3", "-format", "msh2", "inv_mesh_tmp.brep"])
    #run_process([gmsh_path, "inv_mesh_tmp.msh"])


    modify_mesh("inv_mesh_tmp.msh", "inv_mesh.msh")

    #print("test DONE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    return True


if __name__ == "__main__":
    main()
