from genie.core import ares_parser
from genie.core.global_const import GenieMethod

import os
from enum import IntEnum
from typing import List, Dict, Optional
import attr
from genie.core import json_data
import obspy


@json_data.jsondata
class Electrode:
    id: int = 0
    offset: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    # st extension
    is_receiver: bool = False


@json_data.jsondata
class ElectrodeGroup:
    gallery: str = ""
    wall: str = ""
    height: str = ""
    electrodes: List[Electrode] = attr.ib(factory=list)
    measurement_ids: List[int] = attr.ib(factory=list)


@json_data.jsondata
class Measurement:
    number: str = ""
    """Measurement number, this is key"""
    date: str = ""
    file: str = ""
    el_start: int = 0
    el_stop: int = 0
    meas_map: Dict[str, int] = attr.ib(factory=dict)
    eg_ids: List[int] = attr.ib(factory=list)
    el_ids: List[int] = attr.ib(factory=list)
    el_rec_ids: List[int] = attr.ib(factory=list)

    # st extension
    source_id: int = 0
    receiver_start: int = 0
    receiver_stop: int = 0
    channel_start: int = 0

    def __attrs_post_init__(self):
        self.data = None

    def load_data(self, genie):
        """Loads data file."""
        prj_dir = genie.cfg.current_project_dir
        if genie.method == GenieMethod.ERT:
            file = os.path.join(prj_dir, "measurements", self.number, self.file)
            if file == "" or not os.path.isfile(file):
                return
            res = ares_parser.parse(file)

            # remove wrong readings
            #res["data"] = res["data"].drop(res["data"][res["data"]['V'] < 0].index)
            # zakomentovano kvuli analyse_measurement_dialog.py

            # assume that electrode indexes are integers
            # res["data"]['ca'] = res["data"]['ca'].apply(lambda x: int(x))
            # res["data"]['cb'] = res["data"]['cb'].apply(lambda x: int(x))
            # res["data"]['pa'] = res["data"]['pa'].apply(lambda x: int(x))
            # res["data"]['pb'] = res["data"]['pb'].apply(lambda x: int(x))

            if not res["errors"]:
                self.data = res
        else:
            file = os.path.join(prj_dir, "measurements", self.file)
            if file == "" or not os.path.isfile(file):
                return
            st = obspy.read(file, format="SEG2")
            self.data = {"data": st}


@json_data.jsondata
class MeshCutToolParam:
    origin_x: float = 0.0
    origin_y: float = 0.0
    gen_vec1_x: float = 40.0
    gen_vec1_y: float = 0.0
    gen_vec2_x: float = 0.0
    gen_vec2_y: float = 20.0
    z_min: float = 10.0
    z_max: float = 40.0
    margin: float = 5.0
    no_inv_factor: float = 2.0


@json_data.jsondata
class SideViewToolParam:
    origin_x: float = 0.0
    origin_y: float = 0.0
    dir_vec_x: float = 0.0
    dir_vec_y: float = 20.0


class MeshFrom(IntEnum):
    GALLERY_CLOUD = 1
    SURFACE_CLOUD = 2
    GALLERY_MESH = 3


@json_data.jsondata
class InversionParam:
    # bert/gimli params
    verbose: bool = True
    absoluteError: float = 0.001
    relativeError: float = 0.03
    meshFile: str = ""
    meshFrom: MeshFrom = MeshFrom.GALLERY_CLOUD
    reconstructionDepth: int = 6
    smallComponentRatio: float = 0.1
    edgeLength: float = 1.0
    elementSize_d: float = 0.5
    elementSize_D: float = 10.0
    elementSize_H: float = 5.0
    refineMesh: bool = True
    refineP2: bool = False
    omitBackground: bool = False
    depth: Optional[float] = None
    quality: float = 34.0
    maxCellArea: float = 0.0
    paraDX: float = 0.3
    snapDistance: float = 1.0
    useOnlyVerified: bool = False
    minModel: float = 10.0
    maxModel: float = 1e+5
    zWeight: float = 0.7
    lam: float = 20.0
    optimizeLambda: bool = True
    maxIter: int = 20
    robustData: bool = False
    blockyModel: bool = False
    recalcJacobian: bool = True
    local_coord: bool = False
    p3d: bool = False
    p3dStep: float = 1.0

    # test params
    data_log: bool = True
    k_ones: bool = False


@json_data.jsondata
class MeasurementInfoItem:
    measurement_number: str = ""

    # from measurement file
    ca: str = ""
    cb: str = ""
    pa: str = ""
    pb: str = ""
    I: float = 0.0
    V: float = 0.0
    AppRes: float = 0.0
    std: float = 0.0

    # electrode id in inversion input.dat
    inv_ca: int = 0
    inv_cb: int = 0
    inv_pa: int = 0
    inv_pb: int = 0


@json_data.jsondata
class MeasurementsInfo:
    items: List[MeasurementInfoItem] = attr.ib(factory=list)


@json_data.jsondata
class MeasurementModelInfoItem:
    measurement_number: str = ""

    ca: str = ""
    cb: str = ""
    pa: str = ""
    pb: str = ""

    app_res_model: float = 0.0
    app_res_start_model: float = 0.0


@json_data.jsondata
class MeasurementsModelInfo:
    items: List[MeasurementModelInfoItem] = attr.ib(factory=list)
