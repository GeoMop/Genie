import ares_parser

import os
from typing import List
import attr
import json_data


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

    def __attrs_post_init__(self):
        self.data = None

    def load_data(self):
        """Loads data file."""
        if self.file == "" or not os.path.isfile(self.file):
            return
        res = ares_parser.parse(self.file)

        # remove wrong readings
        res["data"] = res["data"].drop(res["data"][res["data"]['V'] < 0].index)

        # assume that electrode indexes are integers
        res["data"]['ca'] = res["data"]['ca'].apply(lambda x: int(x))
        res["data"]['cb'] = res["data"]['cb'].apply(lambda x: int(x))
        res["data"]['pa'] = res["data"]['pa'].apply(lambda x: int(x))
        res["data"]['pb'] = res["data"]['pb'].apply(lambda x: int(x))

        if not res["errors"]:
            self.data = res
