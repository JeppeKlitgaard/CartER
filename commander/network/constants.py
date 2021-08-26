from enum import Enum, IntEnum

from commander.network.utils import Format


class SetOperation(str, Enum):
    SUBTRACT = "-"
    EQUAL = "="
    ADD = "+"
    NUL = "0"


class CartID(IntEnum):
    """
    Must pack to an uint8_t.
    """

    NUL = 0
    ONE = 1
    TWO = 2


class ExperimentInfoSpecifier(IntEnum):
    """
    Must pack to an uint8_t.
    """

    NUL = 0
    POSITION_DRIFT = 1
    FAILURE_MODE = 2
    TRACK_LENGTH_STEPS = 3


SPECIFIER_TO_FORMAT: dict[ExperimentInfoSpecifier, Format] = {
    ExperimentInfoSpecifier.NUL: Format.NUL,
    ExperimentInfoSpecifier.POSITION_DRIFT: Format.INT_32,
    ExperimentInfoSpecifier.FAILURE_MODE: Format.INT_8,
    ExperimentInfoSpecifier.TRACK_LENGTH_STEPS: Format.INT_32,
}


class FailureMode(IntEnum):
    """
    Must pack to an int8_t.
    """

    NUL = 0

    MAX_STEPS_REACHED = -128

    POSITION_LEFT = -1
    POSITION_RIGHT = 1

    ANGLE_LEFT = -2
    ANGLE_RIGHT = 2

    IMBALANCE = 50

    OTHER = 127

    def describe(self) -> str:
        return MODE_TO_DESCRIPTOR[self]


MODE_TO_DESCRIPTOR: dict[FailureMode, str] = {
    FailureMode.NUL: "nul",
    FailureMode.MAX_STEPS_REACHED: "steps/max",
    FailureMode.POSITION_LEFT: "position/left",
    FailureMode.POSITION_RIGHT: "position/right",
    FailureMode.ANGLE_LEFT: "angle/left",
    FailureMode.ANGLE_RIGHT: "angle/right",
    FailureMode.IMBALANCE: "imbalance",
}
