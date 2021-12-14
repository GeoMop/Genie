import os


def current_inv_colormap_filename(genie):
    if genie.current_inversion_cfg.colormap_file:
        split_filename = os.path.split(genie.current_inversion_cfg.colormap_file)
        if split_filename[0] == "color_maps":
            filename = os.path.join(genie.cfg.current_project_dir,
                                    genie.current_inversion_cfg.colormap_file)
        else:
            filename = os.path.join(genie.COLORMAPS_DIR, *split_filename[1:])
    else:
        filename = os.path.join(genie.COLORMAPS_DIR, "jet_color_map.json")
    return filename