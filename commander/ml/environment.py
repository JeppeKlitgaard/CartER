from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Optional, Type, TypeVar, cast

import gym
import supersuit as ss
from gym import spaces
from gym.envs.classic_control import rendering
from pettingzoo.utils.env import ParallelEnv

from stable_baselines3.common.vec_env.vec_monitor import VecMonitor

from commander.ml.agent import CartpoleAgent
from commander.ml.agent.agent import SimulatedCartpoleAgent
from commander.ml.constants import Action
from commander.ml.type_aliases import AgentNameT, StepReturn
from commander.type_aliases import ExternalState

EnvT = TypeVar("EnvT", bound="CartpoleEnv")


class CartpoleEnv(ParallelEnv):  # type: ignore [misc]
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
    ):
        self.agents = [agent.name for agent in agents]
        self.possible_agents = self.agents[:]
        self._agents = list(agents)

        self.agent_name_mapping = dict(zip(self.possible_agents, self._agents))

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

    def seed(self, seed: Optional[int] = None) -> list[Any]:
        seeds = [agent.seed() for agent in self._agents]

        return seeds

    def setup(self) -> None:
        """
        Called when environment first initialised.

        Not called after each reset.
        """
        self.total_world_time: float = 0.0

    def reset(self) -> Mapping[str, ExternalState]:
        observations = {}

        for agent in self._agents:
            observations[agent.name] = agent.reset()

        # ## Environment-level resets
        self.steps: int = 0
        self.viewer: Optional[rendering.Viewer] = None
        self.world_time: float = 0.0

        # This needs to be agent names/ids
        self.agents = self.possible_agents[:]

        # Return observations from agent reset
        return observations

    def observe(self, agent: str) -> ExternalState:
        return self.agent_name_mapping[agent].observe()

    def close(self) -> None:
        raise NotImplementedError("This should be overridden")

    def step(self, actions: dict[AgentNameT, Action]) -> StepReturn:
        raise NotImplementedError("This should be overriden")


class SimulatedCartpoleEnv(CartpoleEnv):
    """
    An environment that represents the Cartpole Environment and
    implements simulated physics.
    """
    def __init__(
        self,
        agents: Sequence[CartpoleAgent],
        start_time: float = 0.0,  # s
        timestep: float = 0.02,  # s
        world_size: tuple[float, float] = (-2.5, 2.5),
    ) -> None:
        self.start_time = start_time
        self.timestep = timestep
        self.world_size = world_size

        super().__init__(agents=agents)

    def setup(self) -> None:
        super().setup()

        for agent_name in self.agents:
            agent = self.agent_name_mapping[agent_name]

            assert isinstance(agent, SimulatedCartpoleAgent)

            agent.tau = self.timestep

    def step(self, actions: dict[AgentNameT, Action]) -> StepReturn:
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

        observations = {}
        rewards = {}
        dones = {}
        infos = {}

        for (agent_name, action) in actions.items():
            agent = self.agent_name_mapping[agent_name]

            observation, reward, done, info = agent.step(action)

            observations[agent_name] = observation
            rewards[agent_name] = reward
            dones[agent_name] = done
            infos[agent_name] = info

        # Patch dones such that when any agent is done, all agents are done
        if any(dones.values()):
            dones = {agent_name: True for agent_name in actions.keys()}

        self.world_time += self.timestep
        self.total_world_time += self.timestep
        self.steps += 1

        return observations, rewards, dones, infos


    def render(self, mode: str = "human") -> rendering.Viewer:
        screen_width = 600
        screen_height = 400

        world_width = abs(self.world_size[0] - self.world_size[1])
        scale = screen_width / world_width

        carty = 100  # TOP OF CART
        cartwidth = scale * 1.0
        cartheight = scale * 0.6

        polewidth = scale * 0.2

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
                polelen = scale * (2 * agent.pole_length)
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
            state = agent.observe_as_dict()

            cartx = state["x"] * scale + screen_width / 2.0  # MIDDLE OF CART
            self.carttrans[agent_name].set_translation(cartx, carty)

        for agent_name, pole in self.poles.items():
            agent = self.agent_name_mapping[agent_name]
            state = agent.observe_as_dict()

            self.poletrans[agent_name].set_rotation(-state["theta"])

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



def make_env(base_env: Type[EnvT], *args: Any, num_frame_stacking: int = 1, **kwargs: Any) -> EnvT:
    env = base_env(*args, **kwargs)

    env = ss.frame_stack_v1(env, stack_size=num_frame_stacking)
    env = ss.black_death_v2(env)

    return env


# def make_parallel_env(
#     *args: Any, num_frame_stacking: int = 1, **kwargs: Any
# ) -> SimulatedCartpoleEnv:
#     env = make_env(*args, num_frame_stacking=num_frame_stacking, **kwargs)

#     env = to_parallel(env)
#     env = ss.black_death_v1(env)

#     return env


def make_sb3_env(
    base_env: Type[EnvT], *args: Any, num_frame_stacking: int = 1, **kwargs: Any
) -> gym.vector.VectorEnv:
    """
    Wrappers all the way down...
    """
    env = make_env(base_env, *args, num_frame_stacking=num_frame_stacking, **kwargs)

    env = ss.pettingzoo_env_to_vec_env_v0(env)

    # Note: VecMonitor automatically vectorises it for us, I believe.
    # It doesn't seem to behave nicely without this - probably need another wrapper
    # like concat vec with just one env and 0 cpus
    venv = VecMonitor(env)

    return venv


def get_sb3_env_root_env(env: VecMonitor) -> CartpoleEnv:
    root_env = cast(Any, env).unwrapped.par_env.unwrapped.env

    return cast(CartpoleEnv, root_env)
