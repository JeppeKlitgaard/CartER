"""
Type alises for agents.
"""

from typing import TypedDict, Union


class CommonGoalParams(TypedDict, total=False):
    failure_position: tuple[float, float]  # m
    failure_position_velo: tuple[float, float]  # m/s
    failure_angle: tuple[float, float]  # rad
    failure_angle_velo: tuple[float, float]  # rad/s

    # Swingup
    failure_time_above_threshold: float  # s
    punishment_positional_failure: float

    # Potential
    track_length: Union[int, float]


GoalParams = Union[CommonGoalParams]
