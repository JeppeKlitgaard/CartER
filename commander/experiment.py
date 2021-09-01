"""
Contains types and logic related to the experimental observations.
"""

from abc import ABC
from enum import Enum, IntEnum, auto, unique
from struct import unpack
from typing import cast


@unique
class ExperimentState(Enum):
    STARTING = auto()
    RESETTING = auto()
    RUNNING = auto()
    ENDING = auto()
    ENDED = auto()


@unique
class ObservationType(IntEnum):
    ONE_CARRIAGES = 0
    TWO_CARRIAGES = 1


class Observation(ABC):
    raw_time: bytes  # unsigned long
    raw_observation_type: bytes  # unsigned char

    @property
    def time(self) -> int:
        return cast(int, unpack("L", self.raw_time)[0])

    @staticmethod
    def observation_type_from_raw(raw_observation_type: bytes) -> ObservationType:
        (obs_id,) = unpack("B", raw_observation_type)

        return ObservationType(obs_id)

    @property
    def observation_type(self) -> ObservationType:
        return self.observation_type_from_raw(self.raw_observation_type)


class Observation1Carriages(Observation):
    raw_angle_1: bytes
    raw_angular_speed_1: bytes

    raw_position_1: bytes
    raw_speed_1: bytes


class Observation2Carriages(Observation1Carriages):
    raw_angle_2: bytes
    raw_angular_speed_2: bytes

    raw_position_2: bytes
    raw_speed_2: bytes


OBSERVATION_TYPE_MAP = {
    ObservationType.ONE_CARRIAGES: Observation1Carriages,
    ObservationType.TWO_CARRIAGES: Observation2Carriages,
}
