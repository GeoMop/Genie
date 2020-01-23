import enum
from PyQt5.QtCore import  Qt
from PyQt5 import QtGui


class Event(enum.IntEnum):
    Left = Qt.LeftButton
    Right = Qt.RightButton
    Middle = Qt.MiddleButton
    NoMod = Qt.NoModifier
    Shift = Qt.ShiftModifier
    Ctrl = Qt.ControlModifier
    Alt = Qt.AltModifier


def event_swap_buttons(event, event_type):
    """
    Create copy of mouse 'event' with swapped buttons.
    :param event: QMouseEvent
    :param even_type: QEvent.MouseButtonPress, QEvent.MouseButtonRelease, QEvent.MouseMove
    :return: QMouseEvent with swaped buttons parameters.
    """
    button = event.button()
    if event.button() == Event.Right:
        button = Event.Left
    elif event.button() == Event.Left:
        button = Event.Right
    left_flag = bool( event.buttons() & Event.Left)
    right_flag = bool( event.buttons() & Event.Right)

    new_buttons = event.buttons()
    # set the swapped flags
    new_buttons = (new_buttons & ~Event.Left) | Event.Left * right_flag
    new_buttons = (new_buttons & ~Event.Right) | Event.Right * left_flag
    new_event = QtGui.QMouseEvent(event_type, event.localPos(), button, new_buttons, event.modifiers())
    return new_event
