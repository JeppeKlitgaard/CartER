import numpy as np

import supersuit as ss
from gym import spaces
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector, to_parallel, wrappers
from pettingzoo.utils.conversions import parallel_wrapper_fn

from stable_baselines3 import A2C, PPO


class MyEnv(AECEnv):
    metadata = {}

    def __init__(self):
        self.agents = ["agent_1", "agent_2"]
        self.possible_agents = self.agents[:]

        self.action_spaces = {
            "agent_1": spaces.Discrete(2),
            "agent_2": spaces.Discrete(2),
        }

        _box_limit = np.array([10, 10, 10, 10])

        self.observation_spaces = {
            "agent_1": spaces.Box(-_box_limit, _box_limit),
            "agent_2": spaces.Box(-_box_limit, _box_limit),
        }

        self._agent_selector = agent_selector(self.agents)
        self.agent_selection = self._agent_selector.next()

        self.dones = {"agent_1": False, "agent_2": False}
        self.rewards = {"agent_1": 0, "agent_2": 0}
        self.infos = {"agent_1": {}, "agent_2": {}}
        self._cumulative_rewards = {"agent_1": 0, "agent_2": 0}

    def observe(self, agent):
        return self.observation_spaces[agent].sample()

    def reset(self):
        return self.observe("agent_1")
        # return [self.observe(agent) for agent in self.agents]


def env():
    e = MyEnv()

    e = wrappers.AssertOutOfBoundsWrapper(e)
    e = wrappers.OrderEnforcingWrapper(e)

    return e


parallel_env = parallel_wrapper_fn(env)


if __name__ == "__main__":

    env_ = parallel_env()

    env_ = ss.pettingzoo_env_to_vec_env_v0(env_)
    env_ = ss.concat_vec_envs_v0(env_, 1, 0, base_class="stable_baselines3")

    model = PPO("MlpPolicy", env_, verbose=3)
    model.learn(total_timesteps=50000)
