from xlsreader import json_data
from data_types import MeshCutToolParam, InversionParam
from xlsreader.xls_parser import XlsMeasurementGroup

from typing import List
import attr


@json_data.jsondata
class InversionConfig:
    mesh_cut_tool_param: MeshCutToolParam = attr.ib(factory=MeshCutToolParam)
    checked_measurements: List[str] = attr.ib(factory=list)
    inversion_param: InversionParam = attr.ib(factory=InversionParam)


@json_data.jsondata
class ProjectConfig:
    version: str = "0.2.0-a"

    xls_measurement_groups: List[XlsMeasurementGroup] = attr.ib(factory=list)

    # todo: udelat strukturu
    point_cloud_origin_x: float = 0.0
    point_cloud_origin_y: float = 0.0
    point_cloud_pixmap_x_min: float = 0.0
    point_cloud_pixmap_y_min: float = 0.0
    point_cloud_pixmap_scale: float = 1.0

    inversions: List[str] = attr.ib(factory=list)
    curren_inversion_name: str = ""


@json_data.jsondata
class GenieConfig:
    test: int = 0
    current_project_dir: str = ""
