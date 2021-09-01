from enum import IntEnum, unique
from typing import TypedDict, Union


@unique
class SimulatedInternalStateIdx(IntEnum):
    X = 0
    DX = 1
    THETA = 2
    DTHETA = 3


@unique
class ExperimentalInternalStateIdx(IntEnum):
    X = 0
    THETA = 1


InternalStateIdx = Union[SimulatedInternalStateIdx, ExperimentalInternalStateIdx]

ExternalTotalKnowledgeStateIdx = SimulatedInternalStateIdx


@unique
class ExternalPositionalKnowlegeStateIdx(IntEnum):
    X = 0
    THETA = 1


ExternalStateIdx = Union[ExternalTotalKnowledgeStateIdx, ExternalPositionalKnowlegeStateIdx]


class ExternalTotalKnowledgeStateMap(TypedDict):
    x: float
    dx: float
    theta: float
    dtheta: float


class ExternalPositionalKnowledgeStateMap(TypedDict):
    x: float
    theta: float


ExternalStateMap = Union[ExternalTotalKnowledgeStateMap, ExternalPositionalKnowledgeStateMap]
