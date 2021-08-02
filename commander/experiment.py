from abc import ABC
from struct import unpack
from enum import IntEnum, unique


@unique
class ObservationType(IntEnum):
    ONE_CARRIAGES = 0
    TWO_CARRIAGES = 1


class Observation(ABC):
    raw_time: bytes  # unsigned long
    raw_observation_type: bytes  # unsigned char

    @property
    def time(self) -> int:
        return unpack("L", self.raw_time)[0]

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
