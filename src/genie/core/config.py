from xlsreader import json_data
from .data_types import MeshCutToolParam, InversionParam
from xlsreader.xls_parser import XlsMeasurementGroup
from genie.core.global_const import GenieMethod

from typing import List
import attr


@json_data.jsondata
class FirstArrival:
    file: str = ""
    channel: int = 0
    time: float = 0.0
    use: bool = True


@json_data.jsondata
class InversionConfig:
    mesh_cut_tool_param: MeshCutToolParam = attr.ib(factory=MeshCutToolParam)
    checked_measurements: List[str] = attr.ib(factory=list)
    inversion_param: InversionParam = attr.ib(factory=InversionParam)

    # st extension
    first_arrivals: List[FirstArrival] = attr.ib(factory=list)


@json_data.jsondata
class MapTransform:
    m11: float = 1.0
    m12: float = 0.0
    m21: float = 0.0
    m22: float = 1.0
    dx: float = 0.0
    dy: float = 0.0


@json_data.jsondata
class ProjectConfig:
    version: str = "0.3.0-a"

    method: GenieMethod = GenieMethod.ERT

    # todo: dat do vlastniho souboru
    xls_measurement_groups: List[XlsMeasurementGroup] = attr.ib(factory=list)

    # todo: udelat strukturu
    point_cloud_origin_x: float = 0.0
    point_cloud_origin_y: float = 0.0
    point_cloud_origin_z: float = 0.0
    point_cloud_pixmap_x_min: float = 0.0
    point_cloud_pixmap_y_min: float = 0.0
    point_cloud_pixmap_scale: float = 1.0

    # todo: udelat strukturu
    gallery_mesh_origin_x: float = 0.0
    gallery_mesh_origin_y: float = 0.0
    gallery_mesh_origin_z: float = 0.0

    map_file_name: str = ""
    map_transform: MapTransform = attr.ib(factory=MapTransform)

    inversions: List[str] = attr.ib(factory=list)
    curren_inversion_name: str = ""

    empty: bool = True


@json_data.jsondata
class GenieConfig:
    current_project_dir: str = ""
