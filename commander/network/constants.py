from enum import Enum, IntEnum


class SetOperation(str, Enum):
    SUBTRACT = "-"
    EQUAL = "="
    ADD = "+"
    NUL = "0"


class CartID(IntEnum):
    ONE = 1
    TWO = 2
