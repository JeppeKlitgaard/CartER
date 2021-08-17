from collections.abc import Mapping
from typing import Any

from commander.type_aliases import ExternalState

AgentNameT = str
StepReturn = tuple[
    dict[AgentNameT, ExternalState],  # Observations
    dict[AgentNameT, float],  # Rewards
    dict[AgentNameT, bool],  # Dones
    dict[AgentNameT, Mapping[str, Any]],  # Infos,
]
