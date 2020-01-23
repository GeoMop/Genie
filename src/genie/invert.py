"""
Script for run inversion in separate process.
"""

import json
import psutil
import sys

import numpy as np
#import pybert as pb
import pygimli as pg


def main():
    # read config file
    conf_file = "inv.conf"
    with open(conf_file, "r") as fd:
        conf = json.load(fd)

    # res = pb.Resistivity("input.dat")
    # res.invert()
    # np.savetxt('resistivity.vector', res.resistivity)
    # return

    # load data file
    data = pg.DataContainerERT("input.dat")

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
        error = conf["relativeError"] + conf["absoluteError"] / data('rhoa')

    # create FOP
    fop = pg.DCSRMultiElectrodeModelling(verbose=conf["verbose"])
    fop.setThreadCount(psutil.cpu_count(logical=False))
    fop.setData(data)

    # create Inv
    inv = pg.RInversion(verbose=conf["verbose"], dosave=False)
    # variables tD, tM are needed to prevent destruct objects
    tD = pg.RTransLog()
    tM = pg.RTransLogLU()
    inv.setTransData(tD)
    inv.setTransModel(tM)
    inv.setForwardOperator(fop)

    # mesh
    if conf["meshFile"] == "":
        depth = conf["depth"]
        if depth is None:
            depth = pg.DCParaDepth(data)

        poly = pg.meshtools.createParaMeshPLC(
            data.sensorPositions(), paraDepth=depth, paraDX=conf["paraDX"],
            paraMaxCellSize=conf["maxCellArea"], paraBoundary=2, boundary=2)

        if conf["verbose"]:
            print("creating mesh...")
        mesh = pg.meshtools.createMesh(poly, quality=conf["quality"], smooth=(1, 10))
    else:
        mesh = pg.Mesh(pg.load(conf["meshFile"]))

    mesh.createNeighbourInfos()

    if conf["verbose"]:
        print(mesh)

    sys.stdout.flush()  # flush before multithreading
    fop.setMesh(mesh)
    fop.regionManager().setConstraintType(1)

    if not conf["omitBackground"]:
        if fop.regionManager().regionCount() > 1:
            fop.regionManager().region(1).setBackground(True)

    if conf["meshFile"] == "":
        fop.createRefinedForwardMesh(True, False)
    else:
        fop.createRefinedForwardMesh(conf["refineMesh"], conf["refineP2"])

    paraDomain = fop.regionManager().paraDomain()
    inv.setForwardOperator(fop)  # necessary?

    # inversion parameters
    inv.setData(data('rhoa'))
    inv.setRelativeError(error)
    fop.regionManager().setZWeight(conf['zWeight'])
    inv.setLambda(conf['lam'])
    inv.setMaxIter(conf['maxIter'])
    inv.setRobustData(conf['robustData'])
    inv.setBlockyModel(conf['blockyModel'])
    inv.setRecalcJacobian(conf['recalcJacobian'])

    pc = fop.regionManager().parameterCount()
    startModel = pg.RVector(pc, pg.median(data('rhoa')))

    inv.setModel(startModel)

    # Run the inversion
    sys.stdout.flush()  # flush before multithreading
    model = inv.run()
    resistivity = model(paraDomain.cellMarkers())
    np.savetxt('resistivity.vector', resistivity)
    print("Done.")


if __name__ == "__main__":
    main()
