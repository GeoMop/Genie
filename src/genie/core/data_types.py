from xlsreader import ares_parser

import os
from typing import List, Dict, Optional
import attr
from xlsreader import json_data


@json_data.jsondata
class Electrode:
    id: int = 0
    offset: float = 0.0
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


@json_data.jsondata
class ElectrodeGroup:
    gallery: str = ""
    wall: str = ""
    height: str = ""
    electrodes: List[Electrode] = attr.ib(factory=list)


@json_data.jsondata
class Measurement:
    number: str = ""
    """Measurement number, this is key"""
    date: str = ""
    file: str = ""
    el_start: int = 0
    el_stop: int = 0
    meas_map: Dict[str, int] = attr.ib(factory=dict)

    def __attrs_post_init__(self):
        self.data = None

    def load_data(self, genie):
        """Loads data file."""
        prj_dir = genie.cfg.current_project_dir
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


@json_data.jsondata
class MeshCutToolParam:
    origin_x: float = -622365.0
    origin_y: float = -1128832.0
    gen_vec1_x: float = 50.0
    gen_vec1_y: float = 0.0
    gen_vec2_x: float = 0.0
    gen_vec2_y: float = 23.0
    z_min: float = 15.0
    z_max: float = 35.0
    margin: float = 5.0


@json_data.jsondata
class InversionParam:
    # bert/gimli params
    verbose: bool = True
    absoluteError: float = 0.001
    relativeError: float = 0.03
    meshFile: str = ""
    refineMesh: bool = True
    refineP2: bool = False
    omitBackground: bool = False
    depth: Optional[float] = None
    quality: float = 34.0
    maxCellArea: float = 0.0
    paraDX: float = 0.3
    zWeight: float = 0.7
    lam: float = 20.0
    maxIter: int = 20
    robustData: bool = False
    blockyModel: bool = False
    recalcJacobian: bool = True

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
