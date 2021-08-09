from enum import IntEnum
from typing import TypedDict, Union


class InternalStateIdx(IntEnum):
    X = 0
    DX = 1
    THETA = 2
    DTHETA = 3


ExternalTotalKnowledgeStateIdx = InternalStateIdx


class ExternalPositionalKnowlegeStateIdx(IntEnum):
    X = 0
    THETA = 1


ExternalStateIdx = Union[ExternalTotalKnowledgeStateIdx, ExternalPositionalKnowlegeStateIdx]


class ExternalTotalKnowledgeStateMap(TypedDict):
    x: float
    dx: float
    theta: float
    dtheta: float


class ExternalPositionKnowledgeStateMap(TypedDict):
    x: float
    theta: float


ExternalStateMap = Union[ExternalTotalKnowledgeStateMap, ExternalPositionalKnowlegeStateIdx]
