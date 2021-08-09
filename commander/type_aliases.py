"""
Contains related type aliases.
"""
import numpy.typing as npt

from commander.constants import FLOAT_TYPE

InternalState = npt.NDArray[FLOAT_TYPE]
ExternalState = npt.NDArray[FLOAT_TYPE]
