from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Optional

import gym
import supersuit as ss
from gym import spaces
from gym.envs.classic_control import rendering
from pettingzoo import AECEnv
from pettingzoo.utils import agent_selector, wrappers
from pettingzoo.utils.conversions import to_parallel

from stable_baselines3.common.vec_env.vec_monitor import VecMonitor

from commander.ml.agent import CartpoleAgent
from commander.ml.constants import Action
from commander.type_aliases import State


class CartpoleEnv(AECEnv):  # type: ignore [misc]
    """
    Base Class for all Cartpole environments.
    """

    metadata = {
        "render.modes": ["human", "rgb_array"],
        "name": "Cartpole_v0",
    }

    def __init__(
        self,
        agents: Sequence[CartpoleAgent],
        max_steps: int = 2500,
        start_time: float = 0.0,  # s
        timestep: float = 0.02,  # s
        world_size: tuple[float, float] = (-2.5, 2.5),
    ):
        self._agents = list(agents)
        self.max_steps = max_steps
        self.start_time = start_time
        self.timestep = timestep
        self.world_size = world_size

        self.action_spaces: Mapping[str, spaces.Space] = {
            agent.name: agent.action_space for agent in self._agents
        }
        self.observation_spaces: Mapping[str, spaces.Space] = {
            agent.name: agent.observation_space for agent in self._agents
        }

        self.seed()

        self.setup()

        # Note some key attributes are only set after calling reset!
        self.reset()

    def is_done(self) -> bool:
        # fmt: off
        conditions = (
            any(self.dones.values()),
            self.steps >= self.max_steps,
        )
        # fmt: on

        return any(conditions)

    def seed(self, seed: Optional[int] = None) -> list[Any]:
        seeds = [agent.seed() for agent in self._agents]

        return seeds

    def setup(self) -> None:
        """
        Called when environment first initialised.

        Not called after each reset.
        """
        self.total_world_time: float = 0.0

    def reset(self) -> Mapping[str, State]:
        observations = {}

        for agent in self._agents:
            observations[agent.name] = agent.reset()

        # ## Environment-level resets
        self.steps: int = 0
        self.viewer: Optional[rendering.Viewer] = None
        self.world_time: float = 0.0

        # This needs to be agent names/ids
        self.agents = [agent.name for agent in self._agents]
        self.possible_agents = self.agents[:]

        self.agent_name_mapping = dict(zip(self.possible_agents, self._agents))

        # Initialise agents
        for agent_name in self.agents:
            agent = self.agent_name_mapping[agent_name]

            agent.tau = self.timestep

        # Agent selector
        self._agent_selector = agent_selector(self.agents)
        self.agent_selection = self._agent_selector.next()

        # Agent -> done status mapping
        self.rewards: dict[str, float] = {agent.name: 0 for agent in self._agents}
        self._cumulative_rewards: dict[str, float] = {agent.name: 0 for agent in self._agents}
        self.dones: dict[str, bool] = {agent.name: False for agent in self._agents}
        self.infos: dict[str, Mapping[str, Any]] = {
            agent.name: agent.info for agent in self._agents
        }


        # Return observations from agent reset
        return observations

    def observe(self, agent: str) -> State:
        return self.agent_name_mapping[agent].observe()

    def close(self) -> None:
        raise NotImplementedError("This should be overridden")

    def step(self, actions: Action) -> None:
        raise NotImplementedError("This should be overriden")


class SimulatedCartpoleEnv(CartpoleEnv):
    """
    An environment that represents the Cartpole Environment and
    implements simulated physics.
    """

    def step(self, action: Action) -> None:
        """
        Performs a single step in the environment using the currently selector agent
        to perform the given action.

        The state information available to our agent is the position of the
        cart and the angle of the pole as well as their first derivatives.

        Using the approach described in Florian's paper
        https://coneural.org/florian/papers/05_cart_pole.pdf

        We are able to obtain the second derivatives of position and angle as
        well.

        These can then be numerically integrated to update the environment
        based on the action.
        """

        if self.dones[self.agent_selection]:
            # If any agent done, all should be done
            self.dones = {agent_name: True for agent_name in self.dones}

            # We thus remove all agents in within one cycle

            self._was_done_step(action)
            return

        agent = self.agent_selection

        # First agent in reward cycle, reset previous rewards
        if self._agent_selector.is_first():
            self.steps += 1

            self._clear_rewards()


        observation, reward, done, info = self.agent_name_mapping[agent].step(action)

        # ## Update environment-level data
        self.rewards[agent] += reward

        # Put rewards into cumulative_rewards
        self._accumulate_rewards()

        # Last agent step in reward cycle
        if self._agent_selector.is_last():
            self.world_time += self.timestep
            self.total_world_time += self.timestep

            for agent_name in self.agents:
                agent = self.agent_name_mapping[agent_name]

                # If agent is done, set all as done
                self.dones[agent_name] = agent.check_state(agent.observe()) or self.is_done()


        self.agent_selection = self._agent_selector.next()

    def render(self, mode: str = "human") -> rendering.Viewer:
        screen_width = 600
        screen_height = 400

        world_width = abs(self.world_size[0] - self.world_size[1])
        scale = screen_width / world_width

        carty = 100  # TOP OF CART
        cartwidth = 50.0
        cartheight = 30.0

        polewidth = 10.0

        axleoffset = cartheight / 4.0

        if self.viewer is None:

            self.viewer = rendering.Viewer(screen_width, screen_height)

            self.carts = {}
            self.carttrans = {}
            self.poles = {}
            self.poletrans = {}
            self.polelens = {}
            self.axles = {}
            for agent_name in self.agents:

                agent = self.agent_name_mapping[agent_name]

                # Cart
                l, r, t, b = -cartwidth / 2, cartwidth / 2, cartheight / 2, -cartheight / 2
                cart = rendering.FilledPolygon([(l, b), (l, t), (r, t), (r, b)])
                carttrans = rendering.Transform()

                # Pole
                polelen = scale * (2 * agent.length)
                l, r, t, b = -polewidth / 2, polewidth / 2, polelen - polewidth / 2, -polewidth / 2
                pole = rendering.FilledPolygon([(l, b), (l, t), (r, t), (r, b)])
                poletrans = rendering.Transform(translation=(0, axleoffset))

                # Axle
                axle = rendering.make_circle(polewidth / 2)

                # Transformations
                cart.add_attr(carttrans)

                pole.add_attr(poletrans)
                pole.add_attr(carttrans)

                axle.add_attr(poletrans)
                axle.add_attr(carttrans)

                # Appearance
                pole.set_color(0.8, 0.6, 0.4)
                axle.set_color(0.5, 0.5, 0.8)

                # Add geometry
                self.viewer.add_geom(cart)
                self.viewer.add_geom(pole)
                self.viewer.add_geom(axle)

                self.carts[agent_name] = cart
                self.carttrans[agent_name] = carttrans
                self.poles[agent_name] = pole
                self.poletrans[agent_name] = poletrans
                self.polelens[agent_name] = polelen
                self.axles[agent_name] = axle

            track = rendering.Line((0, carty), (screen_width, carty))
            track.set_color(0, 0, 0)

            self.viewer.add_geom(track)

        if self.state is None:
            return None

        for pole, polelen in zip(self.poles.values(), self.polelens.values()):
            l, r, t, b = -polewidth / 2, polewidth / 2, polelen - polewidth / 2, -polewidth / 2
            pole.v = [(l, b), (l, t), (r, t), (r, b)]

        for agent_name, cart in self.carts.items():
            agent = self.agent_name_mapping[agent_name]
            state = agent.observe()

            cartx = state[0] * scale + screen_width / 2.0  # MIDDLE OF CART
            self.carttrans[agent_name].set_translation(cartx, carty)

        for agent_name, pole in self.poles.items():
            agent = self.agent_name_mapping[agent_name]
            state = agent.observe()

            self.poletrans[agent_name].set_rotation(-state[2])

        return self.viewer.render(return_rgb_array=mode == "rgb_array")

    def close(self) -> None:
        if self.viewer:
            self.viewer.close()
            self.viewer = None


class ExperimentalCartpoleEnv(CartpoleEnv):
    """
    An environment that represents the Cartpole Environment and
    implements networking with the physical experiment.
    """


def make_env(*args: Any, **kwargs: Any) -> SimulatedCartpoleEnv:
    env = SimulatedCartpoleEnv(*args, **kwargs)

    env = wrappers.AssertOutOfBoundsWrapper(env)
    env = wrappers.OrderEnforcingWrapper(env)

    return env


def make_parallel_env(*args: Any, **kwargs: Any) -> SimulatedCartpoleEnv:
    env = make_env(*args, **kwargs)


    env = to_parallel(env)
    return env


def make_sb3_env(*args: Any, **kwargs: Any) -> gym.vector.VectorEnv:
    """
    Wrappers all the way down...
    """
    env = make_parallel_env(*args, **kwargs)

    env = ss.pettingzoo_env_to_vec_env_v0(env)

    # Note: VecMonitor automatically vectorises it for us, I believe.
    # It doesn't seem to behave nicely without this - probably need another wrapper
    # like concat vec with just one env and 0 cpus
    env = VecMonitor(env)

    return env
