"""
Module for global constants.

Do not use imports (except standard library) in this file. We don't want possible import problems.
"""


from enum import IntEnum


class GenieMethod(IntEnum):
    ERT = 1
    ST = 2


GENIE_PROJECT_FILE_NAME = "genie.prj"
"""Genie project file name"""
