"""
Implements extra Tensorboard metrics.
"""

from stable_baselines3.common.callbacks import BaseCallback


class SimulatedTimeCallback(BaseCallback):
    def __init__(self, verbose=0):
        super().__init__(verbose)

    def _init_callback(self) -> None:
        # There doesn't seem to be a good way of getting back to root env
        self.root_env = self.training_env.unwrapped.vec_envs[0].par_env.aec_env.env.env.env

        return super()._init_callback()

    def _on_step(self) -> bool:
        self.logger.record("custom/world_time", self.root_env.world_time)
        self.logger.record("custom/total_world_time", self.root_env.total_world_time)

        return True
