"""
Contains related type aliases.
"""
from __future__ import annotations

from typing import Any

import numpy.typing as npt

from commander.constants import FLOAT_TYPE
from commander.ml.constants import FailureDescriptors

AgentNameT = str

InternalState = npt.NDArray[FLOAT_TYPE]
ExternalState = npt.NDArray[FLOAT_TYPE]

StateChecks = dict[FailureDescriptors, bool]

StepInfo = dict[str, Any]
StepReturn = tuple[
    dict[AgentNameT, ExternalState],  # Observations
    dict[AgentNameT, float],  # Rewards
    dict[AgentNameT, bool],  # Dones
    dict[AgentNameT, StepInfo],  # Infos,
]
