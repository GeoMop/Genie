"""
json_data module provides decorator for generic serialization/deserialiation
of classes with elementaty type checking.

Rules:
- classes are converted into dictionaries, tuples to the lists and scalar types (str, float, int, bool) and then
  serialized/deserialized  to/from JSON format.

- Definition of serialized attributes is like in attrs library.

- Attributes with type Any can get any value from input, no checks or conversions are performed.

- Lists may have specified type of elements, setting just single element:
    List[ int ]
    List[ Union( [ A, B ] ) ]

- x: Union[ A, B ]
  Input for attribute x should be a dictionary, that should contain key '__class__' which
  must be name of a class containd in the Union. The class of that name is constructed using deserialization recoursively.
  For class_lists of length 1, the '__class__' key is optional.

- Attribute without defaut value is obligatory on input.


Example:
from gm_base.json_data import jsondata
from typing import Union

@jsondata
class Animal:
    n_legs: int = 4       # Default value, optional on input.
    n_legs: int           # Just type, input value obligatory
    length: float         # floats are initializble also from ints

    head: Chicken         # Construct Chicken form the value
    head: Union[ Chicken, Duck, Goose ] # construct one of given types according to '__class__' key on input


TODO:
- Distinguish asserts (check consistancy of code, can be safely removed in production code) and
input checks (these should be tested through explicit if (...): raise ...)

"""

from enum import IntEnum
import inspect
import attr
from typing import Union, Any, List, Tuple, Dict
import builtins


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class WrongKeyError(Error):
    """Raised when attempt assign data to key that not exist"""
    def __init__(self, key):
        self.key = key

    def __str__(self):
        return "'{}'".format(self.key)


_JSON_DATA_TAG = "__jsondata_tag__"


def jsondata(cls=None):
    """
    Decorator for various data classes.
    These classes are basically just documented dictionaries,
    which are JSON serializable and provide some syntactic sugar
    (see DotDict from Flow123d - Jan Hybs)
    In order to simplify also serialization of non-data classes, we
    should implement serialization of __dict__.

    Why use JSON for serialization? (e.g. instead of pickle)
    We want to use it for both sending the data and storing them in files,
    while some of these files should be human readable/writable.
    """

    def wrap(cls):
        # apply attrs
        cls = attr.s(cls, auto_attribs=True)

        # check type of attributes
        for at in cls.__attrs_attrs__:
            _check_type(at.type)

        # mark decorated class
        setattr(cls, _JSON_DATA_TAG, None)

        # add serialize/deserialize methods
        cls.deserialize = classmethod(_deserialize)
        cls.serialize = _serialize

        return cls

    if cls is None:
        return wrap

    return wrap(cls)


def _check_type(type):
    """Checks if type is supported by json data."""
    # base types
    base = [str, float, int, bool]
    for b in base:
        if type is b:
            return

    # json data
    if hasattr(type, _JSON_DATA_TAG):
        return

    # IntEnum
    if inspect.isclass(type) and issubclass(type, IntEnum):
        return

    # List
    if hasattr(type, "__origin__") and type.__origin__ is list:
        _check_type(type.__args__[0])
        return

    # Tuple
    if hasattr(type, "__origin__") and type.__origin__ is tuple:
        for t in type.__args__:
            _check_type(t)
        return

    # Dict
    if hasattr(type, "__origin__") and type.__origin__ is dict and type.__args__[0] is str:
        _check_type(type.__args__[1])
        return

    # Any
    # if type is Any:
    #     return

    # Union
    if hasattr(type, "__origin__") and type.__origin__ is Union:
        args = list(type.__args__)

        # Optional
        if args[-1] is builtins.type(None):
            if len(args) == 2:
                _check_type(args[0])
                return
            args = args[:-1]

        # class factory
        for t in args:
            if not hasattr(t, _JSON_DATA_TAG):
                break
        else:
            return

    raise Exception("Bad type format.")


def _deserialize(cls, config, path=[]):
    """Factory method for creating object from config dictionary."""
    config = config.copy()
    config.pop("__class__", None)

    new_config = {}
    for at in cls.__attrs_attrs__:
        if at.name in config:
            new_config[at.name] = _deserialize_item(at.type, config.pop(at.name), path + [at.name])
        elif at.default is attr.NOTHING:
            raise Exception("Missing obligatory key, path: {}".format(path + [at.name]))

    if config.keys():
        raise WrongKeyError("Keys {} not serializable attrs of dict:\n{}\n{}"
                            .format(list(config.keys()), [at.name for at in cls.__attrs_attrs__], path))

    return cls(**new_config)


def _deserialize_item(type, value, path):
    """
    Deserialize value.

    :param type: type for assign value
    :param value: value for deserialization
    :return:
    """
    # Union
    if hasattr(type, "__origin__") and type.__origin__ is Union:
        args = list(type.__args__)

        # Optional
        if args[-1] is builtins.type(None):
            # Explicitely no value for a optional key.
            if value is None:
                return None

            args = args[:-1]

        # ClassFactory - class given by '__class__' key.
        if len(args) > 1:
            assert "__class__" in value, "Missing '__class__' key to construct one of: {}\npath: {}".format(
                [a.name for a in args], path)

            t = None
            for a in args:
                if a.__name__ == value["__class__"]:
                    t = a
                    break
            else:
                assert False, "Input class: {} not in the Union list: {}\npath: {} ".format(
                    value["__class__"], [a.name for a in args], path)

            return t.deserialize(value, path)
        else:
            type = args[0]

    # JsonData
    if hasattr(type, _JSON_DATA_TAG):
        return type.deserialize(value, path)

    # No check.
    elif type is Any:
        return value

    # list
    elif hasattr(type, "__origin__") and type.__origin__ is list:
        assert value.__class__ is list
        l = []
        for ival, v in enumerate(value):
            l.append(_deserialize_item(type.__args__[0], v, path + [str(ival)]))
        return l

    # tuple
    elif hasattr(type, "__origin__") and type.__origin__ is tuple:
        assert isinstance(value, (list, tuple)), "Expecting list, get class: {}\npath: {}".format(value.__class__, path)
        assert len(type.__args__) == len(value), "Length of tuple do not match: {} != {}".format(len(type.__args__), len(value))
        l = []
        for i, typ, val in zip(range(len(value)), type.__args__, value):
            l.append(_deserialize_item(typ, val, path + [str(i)]))
        return tuple(l)

    # dict
    elif hasattr(type, "__origin__") and type.__origin__ is dict:
        assert value.__class__ is dict
        d = {}
        for k, v in value.items():
            d[k] = _deserialize_item(type.__args__[1], v, path + [k])
        return d

    # other scalar types
    else:
        # IntEnum
        if issubclass(type, IntEnum):
            if value.__class__ is str:
                return type[value]
            elif value.__class__ is int:
                return type(value)
            elif isinstance(value, type):
                return value
            else:
                assert False, "{} is not value of IntEnum: {}\npath: {}".format(value, type, path)

        else:
            try:
                filled_template = type(value)
            except:
                raise Exception("Can not convert value {} to type {}.\npath: {}".format(value, type, path))
            return filled_template


def _serialize(self):
    """
    Serialize the object.
    :return:
    """
    return _get_dict(self)


def _get_dict(obj):
    """Return dict for serialization."""
    sa = [at.name for at in obj.__attrs_attrs__]
    d = {"__class__": obj.__class__.__name__}
    for k, v in obj.__dict__.items():
        if k in sa:
            d[k] = _serialize_object(v)
    return d


def _serialize_object(obj):
    """Prepare object for serialization."""
    if hasattr(obj.__class__, _JSON_DATA_TAG):
        return _get_dict(obj)
    elif isinstance(obj, IntEnum):
        return obj.name
    elif isinstance(obj, dict):
        d = {}
        for k, v in obj.items():
            d[k] = _serialize_object(v)
        return d
    elif isinstance(obj, list) or isinstance(obj, tuple):
        l = []
        for v in obj:
            l.append(_serialize_object(v))
        return l
    else:
        return obj
