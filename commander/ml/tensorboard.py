"""
Implements extra Tensorboard metrics.
"""

from stable_baselines3.common.callbacks import BaseCallback


class SimulatedTimeCallback(BaseCallback):
    """
    Adds simulated world time to tensorboard.
    """
    def __init__(self, verbose=0):
        super().__init__(verbose)

    def _on_step(self) -> bool:
        root_env = self.training_env.unwrapped.vec_envs[0].par_env.unwrapped
        self.logger.record("custom/world_time", root_env.world_time)
        self.logger.record("custom/total_world_time", root_env.total_world_time)

        return True
