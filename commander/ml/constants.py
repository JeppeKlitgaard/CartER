"""
Contains constants for the ML setup.
"""

from enum import IntEnum

import numpy as np

FLOAT_TYPE = np.float64


class Action(IntEnum):
    FORWARDS = 0
    BACKWARDS = 1
