"""
Contains enumeration constants related to the numerical integration code.
"""

from enum import Enum, unique


@unique
class IntegratorOptions(str, Enum):
    RK45 = "RK45"
    LSODA = "LSODA"
