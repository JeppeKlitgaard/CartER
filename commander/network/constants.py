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

    ONE = 1
    TWO = 2


class ExperimentInfoSpecifier(IntEnum):
    """
    Must pack to an uint8_t.
    """

    NUL = 0
    POSITION_DRIFT = 1


SPECIFIER_TO_FORMAT: dict[ExperimentInfoSpecifier, Format] = {
    ExperimentInfoSpecifier.POSITION_DRIFT: Format.INT_32,
    ExperimentInfoSpecifier.NUL: Format.NUL,
}


class FailureMode(IntEnum):
    """
    Must pack to an int8_t.
    """

    NUL = 0

    POSITION_LEFT = -1
    POSITION_RIGHT = 1

    ANGLE_LEFT = -2
    ANGLE_RIGHT = 2

    OTHER = 127
