"""
Implements extra Tensorboard metrics.
"""
import logging
from typing import Any, cast

import gym
import torch as th

from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.logger import Logger, Video

logger = logging.getLogger(__name__)


class GeneralCartpoleMLCallback(BaseCallback):
    """
    Adds a few general metrics to Tensorboard
    """

    FAILURE_MODE_TO_NUM: dict[str, int] = {
        "position/right": 1,
        "position/left": 2,
        "steps/max": 10,
        "multiple": 0,
        "angle/right": -1,
        "angle/left": -2,
    }

    FAILURE_CATEGORY_TO_NUM: dict[str, int] = {
        "position": 1,
        "angle": -1,
        "multiple": 0,
        "steps": 10,
    }

    def _on_step(self) -> bool:
        assert isinstance(self.logger, Logger)

        for infos in self.locals["infos"]:
            # Angle drift
            if angle_drift := infos.get("angle_drift"):
                self.logger.record("cartpoleml/angle_drift", angle_drift)

            # Position drift
            if position_drift := infos.get("position_drift"):
                self.logger.record("cartpoleml/position_drift", position_drift)

        failure_modes = []
        for info in self.locals["infos"]:
            assert "agent_name" in info.keys()
            name = info["agent_name"]

            # Available memory
            if info.get("available_memory") is not None:
                self.logger.record("cartpoleml/available_memory", info["available_memory"])

            # Available memory
            if info.get("serial_in_waiting") is not None:
                self.logger.record("cartpoleml/serial_rx_queue", info["serial_in_waiting"])

            # Episode
            if info.get("environment_episode") is not None:
                self.logger.record("time/env_episode", info["environment_episode"])

            # World time
            if info.get("world_time") is not None:
                self.logger.record("time/world_time", info["world_time"])

            # Total world time
            if info.get("total_world_time") is not None:
                self.logger.record("time/total_world_time", info["total_world_time"])

            # Observation frequency
            if info.get("observation_frequency") is not None:
                self.logger.record("time/observation_frequency", info["observation_frequency"])

            # Observation interval
            if info.get("observation_interval") is not None:
                self.logger.record("time/observation_interval", info["observation_interval"])

            # Action frequency
            if info.get("action_frequency") is not None:
                self.logger.record("time/action_frequency", info["action_frequency"])

            # Action interval
            if info.get("action_interval") is not None:
                self.logger.record("time/action_interval", info["action_interval"])

            # Failure Modes
            if "failure_modes" in info.keys():
                failure_modes.extend(info["failure_modes"])

            # x
            if info.get("x") is not None:
                self.logger.record(f"cartpoleml/x_{name}", info["x"])

            # theta
            if info.get("theta") is not None:
                self.logger.record(f"cartpoleml/theta_{name}", info["theta"])

        failure_mode: str
        if not failure_modes:
            return True
        elif len(failure_modes) > 1:
            failure_mode = "multiple"
        else:
            failure_mode = failure_modes[0]

        if failure_mode not in self.FAILURE_MODE_TO_NUM:
            logger.warn(f"Bad failure mode: {failure_mode}")

        failure_category = failure_mode.split("/")[0]

        self.logger.record(f"cartpoleml/failure_descriptor_text_{name}", failure_mode)
        self.logger.record(
            f"cartpoleml/failure_descriptor_num_{name}", self.FAILURE_MODE_TO_NUM[failure_mode]
        )

        self.logger.record(f"cartpoleml/failure_category_text_{name}", failure_category)
        self.logger.record(
            f"cartpoleml/failure_category_num_{name}",
            self.FAILURE_CATEGORY_TO_NUM[failure_category],
        )

        return True


class VideoRecorderCallback(BaseCallback):
    def __init__(
        self,
        eval_env: gym.Env,
        render_freq: int,
        n_eval_episodes: int = 1,
        deterministic: bool = True,
    ):
        """
        Records a video of an agent's trajectory traversing ``eval_env`` and logs it to TensorBoard

        :param eval_env: A gym environment from which the trajectory is recorded
        :param render_freq: Render the agent's trajectory every eval_freq call of the callback.
        :param n_eval_episodes: Number of episodes to render
        :param deterministic: Whether to use deterministic or stochastic policy
        """
        super().__init__()
        self._eval_env = eval_env
        self._render_freq = render_freq
        self._n_eval_episodes = n_eval_episodes
        self._deterministic = deterministic

    def _on_step(self) -> bool:
        if self.n_calls % self._render_freq == 0:
            screens = []

            def grab_screens(_locals: dict[str, Any], _globals: dict[str, Any]) -> None:
                """
                Renders the environment in its current state, recording the screen in the
                captured `screens` list

                :param _locals: A dictionary containing all local variables
                    of the callback's scope
                :param _globals: A dictionary containing all global variables
                    of the callback's scope
                """
                screen = self._eval_env.render(mode="rgb_array")
                # PyTorch uses CxHxW vs HxWxC gym (and tensorflow) image convention
                screens.append(screen.transpose(2, 0, 1))

            self.model = cast(BaseAlgorithm, self.model)

            evaluate_policy(
                self.model,
                self._eval_env,
                callback=grab_screens,
                n_eval_episodes=self._n_eval_episodes,
                deterministic=self._deterministic,
            )

            assert isinstance(self.logger, Logger)

            self.logger.record(
                "trajectory/video",
                Video(th.ByteTensor([screens]), fps=40),
                exclude=("stdout", "log", "json", "csv"),
            )
        return True
