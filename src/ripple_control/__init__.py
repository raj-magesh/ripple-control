"""Utilities to control the RippleNeuroMed Explorer Summit."""

__all__ = (
    "USE_TCP",
    "check_xipppy_connection",
    "send_pulse",
    "send_trigger",
    "start_recording",
    "stop_recording",
)

from ._utilities import (
    USE_TCP,
    check_xipppy_connection,
    send_pulse,
    send_trigger,
    start_recording,
    stop_recording,
)
