"""
Contains related type aliases.
"""
from typing import Any, Mapping

import numpy.typing as npt

from commander.constants import FLOAT_TYPE
from commander.ml.constants import FailureDescriptors

InternalState = npt.NDArray[FLOAT_TYPE]
ExternalState = npt.NDArray[FLOAT_TYPE]

StepInfo = tuple[ExternalState, float, bool, Mapping[str, Any]]
StateChecks = dict[FailureDescriptors, bool]
