"""
Script for run points merge in separate process.
"""

import sys
import pymeshlab


def main():
    points_file = sys.argv[1]
    distance = float(sys.argv[2])

    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(points_file)
    ms.merge_close_vertices(threshold=pymeshlab.AbsoluteValue(distance))
    ms.save_current_mesh(points_file, save_vertex_normal=False)


if __name__ == "__main__":
    main()
