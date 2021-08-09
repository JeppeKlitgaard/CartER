from enum import IntEnum
from typing import Union


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
