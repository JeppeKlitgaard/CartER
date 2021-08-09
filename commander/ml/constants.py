"""
Contains constants for the ML setup.
"""

from enum import IntEnum, Enum


class Action(IntEnum):
    FORWARDS = 0
    BACKWARDS = 1


class FailureDescriptors(str, Enum):
    MAX_STEPS_REACHED = "steps/max"

    POSITION_LEFT = "position/left"
    POSITION_RIGHT = "position/right"
    ANGLE_LEFT = "angle/left"
    ANGLE_RIGHT = "angle/right"

    IMBALANCE = "imbalance"
