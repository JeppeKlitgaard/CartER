from abc import ABC, abstractmethod
from typing import Union, cast

import numpy as np

from commander.ml.agent.agent import CartpoleAgent
from commander.ml.agent.type_aliases import GoalParams
from commander.ml.constants import Action, FailureDescriptors
from commander.type_aliases import ExternalState, StateChecks

DEFAULT_GOAL_PARAMS = object()  # Sentinel for default goal params


class AgentGoalMixinBase(CartpoleAgent, ABC):
    """
    Mixin that defines the goals and limits of the agent.

    This should be enough to significantly change the behaviour of the system
    without having to reimplement the mechanical logic.
    """

    def update_goal(
        self,
        goal_params: GoalParams,
    ) -> None:
        ...

    def reset_goal(self) -> None:
        ...

    @abstractmethod
    def reward(self, state: ExternalState) -> float:
        ...

    @abstractmethod
    def _check_state(self, state: ExternalState) -> StateChecks:
        ...

    def pre_step(self, action: Action) -> None:
        ...

    def post_step(self, action: Action) -> None:
        ...


class AgentRewardPotentialGoalMixin(AgentGoalMixinBase):
    """
    Agent is rewarded with a sine potential such that it get no reward at the edges
    and 1 at the centre.
    """

    _DEFAULT_FAILURE_ANGLE = 2 * np.pi * 12 / 360

    _DEFAULT_GOAL_PARAMS: GoalParams = {
        "track_length": 1,
        "failure_position": (-0.5, 0.5),  # m
        "failure_position_velo": (-np.inf, np.inf),  # m/s
        "failure_angle": (
            -_DEFAULT_FAILURE_ANGLE,
            _DEFAULT_FAILURE_ANGLE,
        ),  # rad
        "failure_angle_velo": (-np.inf, np.inf),  # rad/s
    }

    track_length: Union[float, int]

    def update_goal(self, goal_params: GoalParams) -> None:
        self.__dict__ |= goal_params

    def reward(self, state: ExternalState) -> float:
        x = state[self.external_state_idx.X]

        rew = cast(float, np.sin(x / self.track_length * np.pi))
        return rew

    def _check_state(self, state: ExternalState) -> StateChecks:
        x = state[self.external_state_idx.X]
        theta = state[self.external_state_idx.THETA]

        checks = {
            FailureDescriptors.POSITION_LEFT: x < self.failure_position[0],
            FailureDescriptors.POSITION_RIGHT: x > self.failure_position[1],
            FailureDescriptors.ANGLE_RIGHT: theta < self.failure_angle[0],
            FailureDescriptors.ANGLE_LEFT: theta > self.failure_angle[1],
        }

        return checks


class AgentTimeGoalMixin(AgentGoalMixinBase):
    """
    This agent is fails when the cartpole leaves the allowed position region
    or the pole angle leaves the allowed angular region.
    """

    _DEFAULT_FAILURE_ANGLE = 2 * np.pi * 12 / 360

    _DEFAULT_GOAL_PARAMS: GoalParams = {
        "failure_position": (-2.4, 2.4),  # m
        "failure_position_velo": (-np.inf, np.inf),  # m/s
        "failure_angle": (
            -_DEFAULT_FAILURE_ANGLE,
            _DEFAULT_FAILURE_ANGLE,
        ),  # rad
        "failure_angle_velo": (-np.inf, np.inf),  # rad/s
    }

    def update_goal(
        self,
        goal_params: GoalParams,
    ) -> None:

        self.failure_position = goal_params["failure_position"]
        self.failure_position_velo = goal_params["failure_position_velo"]
        self.failure_angle = goal_params["failure_angle"]
        self.failure_angle_velo = goal_params["failure_angle_velo"]

    def reward(self, state: ExternalState) -> float:
        return 1.0

    def _check_state(self, state: ExternalState) -> StateChecks:
        x = state[self.external_state_idx.X]
        theta = state[self.external_state_idx.THETA]

        checks = {
            FailureDescriptors.POSITION_LEFT: x < self.failure_position[0],
            FailureDescriptors.POSITION_RIGHT: x > self.failure_position[1],
            FailureDescriptors.ANGLE_RIGHT: theta < self.failure_angle[0],
            FailureDescriptors.ANGLE_LEFT: theta > self.failure_angle[1],
        }

        return checks


class AgentSwingupGoalMixin(AgentGoalMixinBase):
    """
    This agent is rewarded based on how upright the pole is.
    It fails if the pole has been above the horizontal for more than 10 seconds
    and then falls below the horizon (i.e. it has lost balance)."""

    _DEFAULT_GOAL_PARAMS: GoalParams = {
        "failure_position": (-10.0, 10.0),  # m
        "failure_position_velo": (-np.inf, np.inf),  # m/s
        "failure_angle": (-np.inf, np.inf),  # rad
        "failure_angle_velo": (-np.inf, np.inf),  # rad/s
        "failure_time_above_threshold": 10.0,  # s
        "punishment_positional_failure": 10000,
    }

    tau: float

    def update_goal(
        self,
        goal_params: GoalParams,
    ) -> None:

        self.failure_position = goal_params["failure_position"]
        self.failure_position_velo = goal_params["failure_position_velo"]
        self.failure_angle = goal_params["failure_angle"]
        self.failure_angle_velo = goal_params["failure_angle_velo"]

        self.failure_time_above_threshold: float = goal_params["failure_time_above_threshold"]  # s
        self.punishment_positional_failure: float = goal_params["punishment_positional_failure"]

        self.reset_goal()

    def reset_goal(self) -> None:
        self.time_spent_above_horizon = 0.0

    def reward(self, state: ExternalState) -> float:
        x = state[self.external_state_idx.X]
        theta = state[self.external_state_idx.THETA]

        position_failure = any(
            (
                x < self.failure_position[0],
                x > self.failure_position[1],
            )
        )

        if position_failure:
            reward = -self.punishment_positional_failure
        else:
            reward = ((1.0 + np.sin(theta + np.pi / 2.0)) * 2.0) ** 2

        return reward

    def post_step(self, action: Action) -> None:
        state = self.observe()
        theta = state[self.external_state_idx.THETA]

        if np.sin(theta + np.pi / 2.0) > 0.0:
            self.time_spent_above_horizon += self.tau

    def _check_state(self, state: ExternalState) -> StateChecks:
        x = state[self.external_state_idx.X]

        checks = {
            FailureDescriptors.POSITION_LEFT: x < self.failure_position[0],
            FailureDescriptors.POSITION_RIGHT: x > self.failure_position[1],
            FailureDescriptors.IMBALANCE: self.reward(state) < 0
            and self.time_spent_above_horizon >= self.failure_time_above_threshold,
        }

        return checks
