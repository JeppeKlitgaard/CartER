"""
Implements extra Tensorboard metrics.
"""
from typing import Any, cast

from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import Logger

class SimulatedTimeCallback(BaseCallback):
    """
    Adds simulated world time to tensorboard.
    """

    def __init__(self, verbose: int = 0) -> None:
        super().__init__(verbose)

    def _on_step(self) -> bool:
        # Bit of an ugly hack, but par_env does not bring unwrapping forward
        self.training_env = cast(Any, self.training_env)  # Unwrapping is not nice with typing
        root_env = self.training_env.unwrapped.par_env.unwrapped

        assert isinstance(self.logger, Logger)

        self.logger.record("custom/world_time", root_env.world_time)
        self.logger.record("custom/total_world_time", root_env.total_world_time)

        return True


# flake8: noqa
# class VideoRecorderCallback(BaseCallback):
#     def __init__(
#         self,
#         eval_env: gym.Env,
#         render_freq: int,
#         n_eval_episodes: int = 1,
#         deterministic: bool = True,
#     ):
#         """
#         Records a video of an agent's trajectory traversing ``eval_env`` and logs it to TensorBoard

#         :param eval_env: A gym environment from which the trajectory is recorded
#         :param render_freq: Render the agent's trajectory every eval_freq call of the callback.
#         :param n_eval_episodes: Number of episodes to render
#         :param deterministic: Whether to use deterministic or stochastic policy
#         """
#         super().__init__()
#         self._eval_env = eval_env
#         self._render_freq = render_freq
#         self._n_eval_episodes = n_eval_episodes
#         self._deterministic = deterministic

#     def _on_step(self) -> bool:
#         if self.n_calls % self._render_freq == 0:
#             screens = []

#             def grab_screens(_locals: dict[str, Any], _globals: dict[str, Any]) -> None:
#                 """
#                 Renders the environment in its current state, recording the screen in the captured `screens` list

#                 :param _locals: A dictionary containing all local variables of the callback's scope
#                 :param _globals: A dictionary containing all global variables of the callback's scope
#                 """
#                 screen = self._eval_env.render(mode="rgb_array")
#                 # PyTorch uses CxHxW vs HxWxC gym (and tensorflow) image convention
#                 screens.append(screen.transpose(2, 0, 1))

#             evaluate_policy(
#                 self.model,
#                 self._eval_env,
#                 callback=grab_screens,
#                 n_eval_episodes=self._n_eval_episodes,
#                 deterministic=self._deterministic,
#             )
#             self.logger.record(
#                 "trajectory/video",
#                 Video(th.ByteTensor([screens]), fps=40),
#                 exclude=("stdout", "log", "json", "csv"),
#             )
#         return True
