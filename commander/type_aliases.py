"""
Contains related type aliases.
"""
import numpy.typing as npt

from commander.constants import FLOAT_TYPE
from typing import Any, Mapping

InternalState = npt.NDArray[FLOAT_TYPE]
ExternalState = npt.NDArray[FLOAT_TYPE]

StepInfo = tuple[ExternalState, float, bool, Mapping[str, Any]]
StateChecks = dict[str, bool]
