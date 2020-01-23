import ares_parser

import os


class ElectrodeGroup:
    def __init__(self, gallery="", wall="", height=""):
        self.gallery = gallery
        self.wall = wall
        self.height = height
        self.electrodes = []


class Electrode:
    def __init__(self, id=0, offset=0.0, x=0.0, y=0.0, z=0.0):
        self.id = id
        self.offset = offset
        self.x = x
        self.y = y
        self.z = z


class Measurement:
    def __init__(self, number="", date="", file="", el_start=0, el_stop=0):
        self.number = number
        """Measurement number, this is key"""
        self.date = date
        self.file = file
        self.el_start = el_start
        self.el_stop = el_stop
        self.data = None

    def load_data(self):
        """Loads data file."""
        if self.file == "" or not os.path.isfile(self.file):
            return
        res = ares_parser.parse(self.file)
        if not res["errors"]:
            self.data = res
