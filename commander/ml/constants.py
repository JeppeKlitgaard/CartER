"""
Contains constants for the ML setup.
"""

from enum import Enum, IntEnum, unique


@unique
class Action(IntEnum):
    FORWARDS = 0
    BACKWARDS = 1


@unique
class FailureDescriptors(str, Enum):
    MAX_STEPS_REACHED = "steps/max"

    POSITION_LEFT = "position/left"
    POSITION_RIGHT = "position/right"
    ANGLE_LEFT = "angle/left"
    ANGLE_RIGHT = "angle/right"

    IMBALANCE = "imbalance"
