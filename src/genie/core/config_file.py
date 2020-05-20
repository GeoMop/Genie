"""Library for work with state of Genie application.

.. codeauthor:: Pavel Richter <pavel.richter@tul.cz>
"""

import os
import json


if 'APPDATA' in os.environ:
    __config_dir__ = os.path.join(os.environ['APPDATA'], 'Genie')
else:
    __config_dir__ = os.path.join(os.environ['HOME'], '.genie')


def get_config_file(name, directory=None, cls=None, extension='json'):
    """
    Get config object from filename in config directory

    return: Config object or None (if file not exist)
    """
    if directory is not None:
        directory = os.path.join(__config_dir__, directory)
        if not os.path.isdir(directory):
            return None
    else:
        directory = __config_dir__
    file_name = os.path.join(directory, name+'.'+extension)
    try:
        conf_file = open(file_name, 'r')
    except (FileNotFoundError, IOError):
        return None
    config = json.load(conf_file)
    conf_file.close()
    config = cls.deserialize(config)
    return config


def save_config_file(name, config, directory=None, extension='json'):
    """Save config object to file name.extension in config directory"""
    if directory is not None:
        directory = os.path.join(__config_dir__, directory)
    else:
        directory = __config_dir__
    try:
        os.makedirs(directory, exist_ok=True)
    except:
        raise Exception('Cannot create config directory: ' + directory)
    file_name = os.path.join(directory, name+'.'+extension)
    data = config.serialize()
    conf_file = open(file_name, 'w')
    json.dump(data, conf_file, indent=4, sort_keys=True)
    conf_file.close()


def delete_config_file(name, directory=None, extension='json'):
    """
    Delete config file name.extension from config directory
    """
    if directory is not None:
        directory = os.path.join(__config_dir__, directory)
        if not os.path.isdir(directory):
            return
    else:
        directory = __config_dir__
    file_name = os.path.join(directory, name+'.'+extension)
    try:
        os.remove(file_name)
    except (RuntimeError, IOError):
        return
