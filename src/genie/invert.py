"""
Script for run inversion in separate process.
"""

import json
import psutil
import sys
import os
import subprocess
import time

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from core import snap_electrodes
from core.config import InversionConfig
from core import mesh_gen2
from core import cut_point_cloud
from bgem.gmsh.gmsh_io import GmshIO

import numpy as np
#import pybert as pb
import pygimli as pg


def main():
    # read config file
    conf_file = "inv.conf"
    with open(conf_file, "r") as fd:
        conf = json.load(fd)
    inversion_conf = InversionConfig.deserialize(conf)
    inv_par = inversion_conf.inversion_param
    cut_par = inversion_conf.mesh_cut_tool_param

    #remove_old_files()

    prepare(cut_par)
    #return

    #ball_mesh("inv_mesh.msh", "inv_mesh2.msh", [-622342, -1128822, 22], 5.0)
    #return

    print_headline("Inversion")

    # res = pb.Resistivity("input.dat")
    # res.invert()
    # np.savetxt('resistivity.vector', res.resistivity)
    # return

    # load data file
    data = pg.DataContainerERT("input_snapped.dat")
    #data = pg.DataContainerERT("ldp2.dat")

    # k, rhoa
    if inv_par.k_ones:
        data.set("k", np.ones(data.size()))
    else:
        data.set("k", pg.geometricFactors(data))
    #data.set("err", pb.Resistivity.estimateError(data, absoluteUError=0.0001, relativeError=0.03))
    data.set("rhoa", data("u") / data("i") * data("k"))

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
    if data.allNonZero('err'):
        error = data('err')
    else:
        print("estimate data error")
        error = inv_par.relativeError + inv_par.absoluteError / data('rhoa')

    # create FOP
    fop = pg.DCSRMultiElectrodeModelling(verbose=inv_par.verbose)
    fop.setThreadCount(psutil.cpu_count(logical=False))
    fop.setData(data)

    # create Inv
    inv = pg.RInversion(verbose=inv_par.verbose, dosave=False)
    # variables tD, tM are needed to prevent destruct objects
    tM = pg.RTransLogLU()
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
    inv.setMaxIter(inv_par.maxIter)
    inv.setRobustData(inv_par.robustData)
    inv.setBlockyModel(inv_par.blockyModel)
    inv.setRecalcJacobian(inv_par.recalcJacobian)

    pc = fop.regionManager().parameterCount()
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
    print("Done.")


def coverageDC(fop, inv, paraDomain):
    """
    Return coverage vector considering the logarithmic transformation.
    """
    covTrans = pg.coverageDCtrans(fop.jacobian(),
                                  1.0/inv.response(),
                                  1.0/inv.model())
    return np.log10(covTrans / paraDomain.cellSizes())


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
        "resistivity.vector",
        "resistivity.vtk"
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


def prepare(mesh_cut_tool_param):
    #print("prepare !!!")

    print_headline("Cutting point cloud")
    t = time.time()
    cut_point_cloud.cut_ascii(os.path.join("..", "..", "point_cloud.xyz"), "point_cloud_cut.xyz", mesh_cut_tool_param)
    #cut_point_cloud.cut_ascii("point_cloud_cut_x.xyz", "point_cloud_cut.xyz", mesh_cut_tool_param)
    print("elapsed time: {:0.3f} s".format(time.time() - t))
    #return

    # meshlab
    t = time.time()
    print_headline("Creating gallery mesh")
    meshlabserver_path = '/tmp/.mount_MeshLaDVxn6r'
    os.environ['PATH'] = meshlabserver_path + os.pathsep + os.environ['PATH']
    meshlabserver_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../meshlab/meshlabserver.exe")
    if not os.path.exists(meshlabserver_path):
        meshlabserver_path = "meshlabserver"
    run_process([meshlabserver_path, "-i", "point_cloud_cut.xyz", "-o", "gallery_mesh.ply", "-m", "sa", "-s", os.path.join(os.path.dirname(os.path.realpath(__file__)), "meshlab_script.mlx")])
    print("meshlab elapsed time: {:0.3f} s".format(time.time() - t))

    gmsh_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../gmsh/gmsh.exe")
    if not os.path.exists(gmsh_path):
        gmsh_path = "gmsh"
    run_process([gmsh_path, "-format", "msh2", "-save", "gallery_mesh.ply"])

    print_headline("Snapping electrodes")
    snap_electrodes.main()

    #return
    print_headline("Creating inversion mesh")
    mesh_gen2.gen(mesh_cut_tool_param)

    run_process([gmsh_path, "-3", "-format", "msh2", "inv_mesh_tmp.brep"])
    #run_process([gmsh_path, "inv_mesh_tmp.msh"])


    modify_mesh("inv_mesh_tmp.msh", "inv_mesh.msh")

    #print("test DONE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


if __name__ == "__main__":
    main()


