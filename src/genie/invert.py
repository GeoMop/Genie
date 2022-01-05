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

from genie.core import snap_electrodes, snap_surf
from genie.core.config import InversionConfig, ProjectConfig
from genie.core import mesh_gen, mesh_surf
from genie.core import cut_point_cloud
from genie.core.data_types import MeasurementsInfo, MeshFrom, MeasurementModelInfoItem, MeasurementsModelInfo
from genie.core.global_const import GenieMethod
from genie.core import misc
from bgem.gmsh.gmsh_io import GmshIO
from bgem.gmsh import gmsh, field

import numpy as np
#import pybert as pb
import pygimli as pg
import pymeshlab


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

    ret, bw_surface = prepare(cut_par, inv_par, project_conf)
    if not ret:
        return
    #return

    # snap electrodes
    print()
    print_headline("Snapping electrodes")
    if inv_par.meshFrom == MeshFrom.SURFACE_CLOUD:
        snap_surf.main(inv_par, project_conf, bw_surface, max_dist=inv_par.snapDistance)
    else:
        snap_electrodes.main(inv_par, project_conf, max_dist=inv_par.snapDistance)

    #ball_mesh("inv_mesh.msh", "inv_mesh2.msh", [-622342, -1128822, 22], 5.0)
    #return

    print()
    print_headline("Creating inversion mesh")
    mesh_from_brep("inv_mesh_tmp.brep", "inv_mesh_tmp.msh2", project_conf, inv_par)

    print()
    print_headline("Modify mesh")
    modify_mesh("inv_mesh_tmp.msh2", "inv_mesh.msh", cut_par)

    #if inv_par.meshFrom == MeshFrom.SURFACE_CLOUD:
    print()
    print_headline("Snapping electrodes final")
    snap_electrodes.main(inv_par, project_conf, max_dist=inv_par.snapDistance, final=True)

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
        data.set("k", misc.geometricFactors(data))
    #data.set("err", pb.Resistivity.estimateError(data, absoluteUError=0.0001, relativeError=0.03))
    #data.set("k", np.ones(data.size()))
    #data.set("k", misc.geometricFactors(data))
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
    fop = pg.core.DCSRMultiElectrodeModelling(verbose=inv_par.verbose)
    fop.setThreadCount(psutil.cpu_count(logical=False))
    fop.setData(data)

    # create Inv
    inv = pg.core.RInversion(verbose=inv_par.verbose, dosave=False)
    # variables tD, tM are needed to prevent destruct objects
    tM = pg.core.RTransLogLU(inv_par.minModel, inv_par.maxModel)
    if inv_par.data_log:
        tD = pg.core.RTransLog()
        inv.setTransData(tD)
    inv.setTransModel(tM)
    inv.setForwardOperator(fop)

    # mesh
    mesh_file = "inv_mesh.msh"
    #mesh_file = inv_par.meshFile
    if mesh_file == "":
        depth = inv_par.depth
        if depth is None:
            depth = pg.core.DCParaDepth(data)

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

    if not inv_par.omitBackground:
        if fop.regionManager().regionCount() > 1:
            fop.regionManager().region(1).setBackground(True)

    if mesh_file == "":
        fop.createRefinedForwardMesh(True, False)
    else:
        fop.createRefinedForwardMesh(inv_par.refineMesh, inv_par.refineP2)

    paraDomain = fop.regionManager().paraDomain()
    #paraDomain = fop.regionManager().mesh()
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
    inv.setOptimizeLambda(inv_par.optimizeLambda)
    inv.setMaxIter(inv_par.maxIter)
    inv.setRobustData(inv_par.robustData)
    inv.setBlockyModel(inv_par.blockyModel)
    inv.setRecalcJacobian(inv_par.recalcJacobian)

    pc = fop.regionManager().parameterCount()
    if inv_par.k_ones:
        # hack of gimli hack
        v = pg.Vector(pg.Vector(pc, pg.core.median(data('rhoa') * misc.geometricFactors(data))))
        v[0] += tolerance * 2
        startModel = v
    else:
        startModel = pg.Vector(pc, pg.core.median(data('rhoa')))
    #startModel = pg.RVector(pc, 2000.0)

    inv.setModel(startModel)

    # Run the inversion
    sys.stdout.flush()  # flush before multithreading
    model = inv.run()
    resistivity = model[paraDomain.cellMarkers()]
    np.savetxt('resistivity.vector', resistivity)
    paraDomain.addData('Resistivity', resistivity)
    #paraDomain.addExportData('Resistivity (log10)', np.log10(resistivity))
    #paraDomain.addExportData('Coverage', coverageDC(fop, inv, paraDomain))
    #paraDomain.exportVTK('resistivity')

    # output in local coordinates
    if inv_par.local_coord:
        base_point, gen_vecs = cut_point_cloud.cut_tool_to_gen_vecs(cut_par)
        localparaDomain = pg.Mesh(paraDomain)
        localparaDomain.translate(pg.RVector3(-base_point))
        localparaDomain.rotate(pg.RVector3(0, 0, -math.atan2(gen_vecs[0][1], gen_vecs[0][0])))
        localparaDomain.exportVTK('resistivity')
    else:
        paraDomain.exportVTK('resistivity')

    # measurements on model
    print()
    print_headline("Measurements on model")
    with open("measurements_info.json") as fd:
        meas_info = MeasurementsInfo.deserialize(json.load(fd))

    resp = fop.response(resistivity)
    # hack of gimli hack
    v = pg.Vector(startModel)
    v[0] += tolerance * 2
    resp_start = fop.response(v)

    map = {}
    map_start = {}
    map_appres_gimli = {}
    for i in range(data.size()):
        map[(data("a")[i], data("b")[i], data("m")[i], data("n")[i])] = resp[i]
        map_start[(data("a")[i], data("b")[i], data("m")[i], data("n")[i])] = resp_start[i]
        map_appres_gimli[(data("a")[i], data("b")[i], data("m")[i], data("n")[i])] = data('rhoa')[i]

    meas_model_info = MeasurementsModelInfo()

    with open("measurements_model.txt", "w") as fd:
        fd.write("meas_number ca  cb  pa  pb  I[A]      V[V]     AppRes[Ohmm] std    AppResGimli[Ohmm] AppResModel[Ohmm]   ratio AppResStartModel[Ohmm] start_ratio\n")
        fd.write("-------------------------------------------------------------------------------------------------------------------------------------------------\n")
        for item in meas_info.items:
            k = (item.inv_ca, item.inv_cb, item.inv_pa, item.inv_pb)
            if k in map:
                m_on_m = "{:17.2f} {:17.2f} {:7.2f} {:22.2f}     {:7.2f}".format(map_appres_gimli[k], map[k], map[k]/map_appres_gimli[k], map_start[k], map_start[k]/map_appres_gimli[k])
                meas_model_info.items.append(MeasurementModelInfoItem(measurement_number=item.measurement_number, ca=item.ca, cb=item.cb, pa=item.pa, pb=item.pb, app_res_model=map[k], app_res_start_model=map_start[k]))
            else:
                m_on_m = "         not used"

            fd.write("{:11} {:3} {:3} {:3} {:3} {:8.6f} {:9.6f} {:12.2f} {:6.4f} {}\n".format(item.measurement_number, item.ca, item.cb, item.pa, item.pb, item.I, item.V, item.AppRes, item.std, m_on_m))

    with open("measurements_model_info.json", "w") as fd:
        json.dump(meas_model_info.serialize(), fd, indent=4, sort_keys=True)

    if inv_par.p3d:
        print()
        print_headline("Saving p3d")
        t = time.time()
        save_p3d(paraDomain, model.array(), cut_par, inv_par.p3dStep, "resistivity", inv_par.local_coord)
        print("save_p3d elapsed time: {:0.3f} s".format(time.time() - t))

    print()
    print("All done.")


def inv_st(inversion_conf, project_conf):
    inv_par = inversion_conf.inversion_param
    cut_par = inversion_conf.mesh_cut_tool_param

    remove_old_files()

    ret, bw_surface = prepare(cut_par, inv_par, project_conf)
    if not ret:
        return
    #return

    # snap electrodes
    print()
    print_headline("Snapping electrodes")
    if inv_par.meshFrom == MeshFrom.SURFACE_CLOUD:
        snap_surf.main(inv_par, project_conf, bw_surface, max_dist=inv_par.snapDistance)
    else:
        snap_electrodes.main(inv_par, project_conf, max_dist=inv_par.snapDistance)

    #ball_mesh("inv_mesh.msh", "inv_mesh2.msh", [-622342, -1128822, 22], 5.0)
    #return

    print()
    print_headline("Creating inversion mesh")
    mesh_from_brep("inv_mesh_tmp.brep", "inv_mesh_tmp.msh2", project_conf, inv_par)

    print()
    print_headline("Modify mesh")
    modify_mesh("inv_mesh_tmp.msh2", "inv_mesh.msh", cut_par)

    #if inv_par.meshFrom == MeshFrom.SURFACE_CLOUD:
    print()
    print_headline("Snapping electrodes final")
    snap_electrodes.main(inv_par, project_conf, max_dist=inv_par.snapDistance, final=True)

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
    fop = pg.core.TravelTimeDijkstraModelling(verbose=inv_par.verbose)
    fop.setThreadCount(psutil.cpu_count(logical=False))
    fop.setData(data)

    # create Inv
    inv = pg.core.RInversion(verbose=inv_par.verbose, dosave=False)
    # variables tD, tM are needed to prevent destruct objects
    tM = pg.core.RTransLogLU(1.0 / inv_par.maxModel, 1.0 / inv_par.minModel)
    tD = pg.core.RTrans()
    inv.setTransData(tD)
    inv.setTransModel(tM)
    inv.setForwardOperator(fop)

    # mesh
    mesh_file = "inv_mesh.msh"
    if mesh_file == "":
        depth = inv_par.depth
        if depth is None:
            depth = pg.core.DCParaDepth(data)

        poly = pg.meshtools.createParaMeshPLC(
            data.sensorPositions(), paraDepth=depth, paraDX=inv_par.paraDX,
            paraMaxCellSize=inv_par.maxCellArea, paraBoundary=2, boundary=2)

        if inv_par.verbose:
            print("creating mesh...")
        mesh = pg.meshtools.createMesh(poly, quality=inv_par.quality, smooth=(1, 10))
    else:
        mesh = pg.Mesh(pg.load(mesh_file))

    mesh.createNeighbourInfos()

    mesh.createSecondaryNodes()

    if inv_par.verbose:
        print(mesh)

    sys.stdout.flush()  # flush before multithreading
    fop.setMesh(mesh)
    fop.regionManager().setConstraintType(1)

    if not inv_par.omitBackground:
        if fop.regionManager().regionCount() > 1:
            fop.regionManager().region(1).setBackground(True)

    if mesh_file == "":
        fop.createRefinedForwardMesh(True, False)
    else:
        fop.createRefinedForwardMesh(inv_par.refineMesh, inv_par.refineP2)

    paraDomain = fop.regionManager().paraDomain()
    inv.setForwardOperator(fop)  # necessary?

    # inversion parameters
    inv.setData(data('t'))
    absoluteError = 0.001
    relativeError = 0.001
    inv.setAbsoluteError(absoluteError + data('t') * relativeError)
    #inv.setRelativeError(pg.RVector(data.size(), 0.03))
    fop.regionManager().setZWeight(inv_par.zWeight)
    inv.setLambda(inv_par.lam)
    inv.setOptimizeLambda(inv_par.optimizeLambda)
    inv.setMaxIter(inv_par.maxIter)
    inv.setRobustData(inv_par.robustData)
    inv.setBlockyModel(inv_par.blockyModel)
    inv.setRecalcJacobian(inv_par.recalcJacobian)

    startModel = fop.createDefaultStartModel()
    inv.setModel(startModel)

    # Run the inversion
    sys.stdout.flush()  # flush before multithreading
    model = inv.run()
    velocity = 1.0 / model[paraDomain.cellMarkers()]
    np.savetxt('velocity.vector', velocity)
    paraDomain.addData('Velocity', velocity)
    #paraDomain.exportVTK('velocity')

    # output in local coordinates
    if inv_par.local_coord:
        base_point, gen_vecs = cut_point_cloud.cut_tool_to_gen_vecs(cut_par)
        localparaDomain = pg.Mesh(paraDomain)
        localparaDomain.translate(pg.RVector3(-base_point))
        localparaDomain.rotate(pg.RVector3(0, 0, -math.atan2(gen_vecs[0][1], gen_vecs[0][0])))
        localparaDomain.exportVTK('velocity')
    else:
        paraDomain.exportVTK('velocity')

    if inv_par.p3d:
        print()
        print_headline("Saving p3d")
        t = time.time()
        save_p3d(paraDomain, 1.0 / model.array(), cut_par, inv_par.p3dStep, "velocity", inv_par.local_coord)
        print("save_p3d elapsed time: {:0.3f} s".format(time.time() - t))

    print()
    print("All done.")


def coverageDC(fop, inv, paraDomain):
    """
    Return coverage vector considering the logarithmic transformation.
    """
    covTrans = pg.core.coverageDCtrans(fop.jacobian(),
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


def save_p3d(paraDomain, model_array, mesh_cut_tool_param, step, file_name, local_coord=False):
    """Saves result as .p3d file."""
    base_point, gen_vecs = cut_point_cloud.cut_tool_to_gen_vecs(mesh_cut_tool_param)

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

    if local_coord:
        base_point = np.array([0.0, 0.0, 0.0])
        l0 = np.linalg.norm(gen_vecs[0])
        l1 = np.linalg.norm(gen_vecs[1])
        phi = math.acos((gen_vecs[0][0] * gen_vecs[1][0] + gen_vecs[0][1] * gen_vecs[1][1]) / (l0 * l1))
        gen_vecs[0] = np.array([l0, 0.0, 0.0])
        gen_vecs[1] = np.array([l1 * math.cos(phi), l1 * math.sin(phi), 0.0])

    with open(file_name + ".p3d", "w") as fd_p3d:
        with open(file_name + ".q", "w") as fd_q:
            fd_p3d.write("{} {} {}\n".format(x_nodes, y_nodes, z_nodes))

            fd_q.write("{} {} {}\n".format(x_nodes, y_nodes, z_nodes))
            fd_q.write("{:.10g} {:.10g} {:.10g} {:.10g}\n".format(0.0, 0.0, 0.0, 0.0))

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

            s = "{:.10g}".format(0.0)
            for _ in range(x_nodes * y_nodes * z_nodes * 4):
                q_write(s)

            p3d_finalize()
            q_finalize()


def mesh_from_brep(brep_file, mesh_file, project_conf, inv_par):
    if project_conf.method == GenieMethod.ERT:
        data = pg.DataContainerERT("input_snapped.dat", removeInvalid=False)
    else:
        data = pg.DataContainer("input_snapped.dat", sensorTokens='s g', removeInvalid=False)

    el_pos = []
    for i in range(len(data.sensorPositions())):
        pos = data.sensorPosition(i)
        pos = np.array([pos[0], pos[1], pos[2]])
        el_pos.append(pos)

    model = gmsh.GeometryOCC("model_name")
    compound = model.import_shapes(brep_file, highestDimOnly=False)
    points = [model.point(pos).tags[0] for pos in el_pos]
    dist = field.distance_nodes(points)
    f_distance = field.threshold(dist, lower_bound=(inv_par.elementSize_d, inv_par.elementSize_d),
                                 upper_bound=(inv_par.elementSize_D, inv_par.elementSize_H))
    model.set_mesh_step_field(f_distance)
    model.mesh_options.CharacteristicLengthMin = 0.1
    model.mesh_options.CharacteristicLengthMax = 100
    model.make_mesh([compound])
    model.write_mesh(mesh_file, gmsh.MeshFormat.msh2)


def modify_mesh(in_file, out_file, mesh_cut_tool_param):
    """Keeps only elements of dim 2 and 3. Sets physical id to 2 for inversion region and 1 for no inversion region."""
    el_type_to_dim = {15: 0, 1: 1, 2: 2, 4: 3}

    base_point, gen_vecs = cut_point_cloud.cut_tool_to_gen_vecs(mesh_cut_tool_param, only_inv=True)
    inv_tr_mat = cut_point_cloud.inv_tr(gen_vecs)

    mesh = GmshIO(in_file)

    new_elements = {}
    for id, elm in mesh.elements.items():
        el_type, tags, nodes = elm
        dim = el_type_to_dim[el_type]
        if dim not in [2, 3]:
            continue
        physical_id = 2
        if dim == 3 and mesh_cut_tool_param.no_inv_factor > 1:
            n_inside = 0
            for n in nodes:
                nn = mesh.nodes[n]
                nl = cut_point_cloud.tr_to_local(base_point, inv_tr_mat, np.array([nn[0], nn[1], nn[2]]))
                if 0 <= nl[0] <= 1 and 0 <= nl[1] <= 1 and 0 <= nl[2] <= 1:
                    n_inside += 1
            if n_inside < 4:
                physical_id = 1
        tags[0] = physical_id
        new_elements[id] = (el_type, tags, nodes)
    mesh.elements = new_elements

    with open(out_file, "w") as fd:
        mesh.write_ascii(fd)


def reconst_depth(mesh_cut_tool_param, inv_par):
    base_point, gen_vecs = cut_point_cloud.cut_tool_to_gen_vecs(mesh_cut_tool_param, margin=True)
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

    # max size along all dimensions
    size = max(abs(x_max - x_min), abs(y_max - y_min), abs(z_max - z_min))

    d = math.ceil(math.log2(size / inv_par.edgeLength))

    # apply limits
    if d < 4:
        d = 4
    elif d > 10:
        d = 10

    return d


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
        "inv_mesh_tmp.msh2",
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
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh("point_cloud_cut.xyz")
        ms.compute_normals_for_point_sets()
        ms.surface_reconstruction_screened_poisson(depth=reconst_depth(mesh_cut_tool_param, inv_par))
        ms.select_small_disconnected_component(nbfaceratio=inv_par.smallComponentRatio)
        ms.delete_selected_faces_and_vertices()
        ms.invert_faces_orientation(forceflip=False)
        ms.remove_zero_area_faces()
        ms.remove_duplicate_vertices()
        ms.remeshing_isotropic_explicit_remeshing(
            targetlen=pymeshlab.AbsoluteValue(inv_par.edgeLength),
            maxsurfdist=pymeshlab.AbsoluteValue(inv_par.edgeLength))
        ms.save_current_mesh("gallery_mesh.ply", binary=False)
        print("meshlab elapsed time: {:0.3f} s".format(time.time() - t))

        print()
        print_headline("Converting gallery mesh")
        run_process([gmsh_path, "-format", "msh2", "-save", "gallery_mesh.ply"])


    #return
    bw_surface = None
    print()
    print_headline("Creating inversion geometry")
    if inv_par.meshFrom == MeshFrom.SURFACE_CLOUD:
        ret, bw_surface = mesh_surf.gen(os.path.join("..", "..", "point_cloud.xyz"), "inv_mesh_tmp.brep", mesh_cut_tool_param)
        if not ret:
            return False, bw_surface
    else:
        if inv_par.meshFrom == MeshFrom.GALLERY_CLOUD:
            gallery_mesh_file = "gallery_mesh.msh"
        elif inv_par.meshFrom == MeshFrom.GALLERY_MESH:
            gallery_mesh_file = "../../gallery_mesh.msh"
        #mesh_gen2.gen(mesh_cut_tool_param)
        if not mesh_gen.gen(gallery_mesh_file, "inv_mesh_tmp.brep", mesh_cut_tool_param, inv_par, project_conf):
            print("Error in mesh generation")
            return False, bw_surface

    #run_process([gmsh_path, "-3", "-format", "msh2", "inv_mesh_tmp.brep"])
    #run_process([gmsh_path, "inv_mesh_tmp.msh"])


    #modify_mesh("inv_mesh_tmp.msh2", "inv_mesh.msh")

    #print("test DONE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    return True, bw_surface


if __name__ == "__main__":
    main()
