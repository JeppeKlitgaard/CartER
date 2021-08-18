from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any, Optional, Type, TypeVar, cast

import gym
import supersuit as ss
from gym import spaces
from gym.envs.classic_control import rendering
from pettingzoo.utils.env import ParallelEnv

from stable_baselines3.common.vec_env.vec_monitor import VecMonitor

from commander.ml.agent import CartpoleAgent
from commander.ml.agent.agent import ExperimentalCartpoleAgent, SimulatedCartpoleAgent
from commander.ml.constants import Action
from commander.network import NetworkManager
from commander.network.constants import CartID, SetOperation
from commander.network.protocol import (
    CartSpecificPacket,
    DebugPacket,
    DoJigglePacket,
    ErrorPacket,
    ExperimentStartPacket,
    FindLimitsPacket,
    InfoPacket,
    ObservationPacket,
    SetVelocityPacket,
)
from commander.network.selectors import message_startswith
from commander.type_aliases import AgentNameT, ExternalState, StepInfo, StepReturn
from commander.utils import raises

logger = logging.getLogger(__name__)

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
        defer_reset: bool = True,
    ):
        self.agents = [agent.name for agent in agents]
        self.possible_agents = self.agents[:]
        self._agents = list(agents)

        self.name_to_agent: Mapping[AgentNameT, CartpoleAgent] = dict(
            zip(self.possible_agents, self._agents)
        )

        self.action_spaces: Mapping[str, spaces.Space] = {
            agent.name: agent.action_space for agent in self._agents
        }
        self.observation_spaces: Mapping[str, spaces.Space] = {
            agent.name: agent.observation_space for agent in self._agents
        }

        self.seed()

        self.setup()

        # Note some key attributes are only set after calling reset!
        if not defer_reset:
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
        return self.name_to_agent[agent].observe()

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
        agents: Sequence[SimulatedCartpoleAgent],
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
            agent = self.name_to_agent[agent_name]

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

        for agent_name, action in actions.items():
            agent = self.name_to_agent[agent_name]

            info = agent.step(action)
            observation = agent.observe()

            checks = agent.check_state(observation)
            done = any(checks.values())

            reward = agent.reward(observation) if not done else 0.0

            if done:
                failure_modes = [k.value for k, v in checks.items() if v]
                logger.info(f"Failure modes: {failure_modes}")

                info["failure_modes"] = failure_modes

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

                agent = self.name_to_agent[agent_name]

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
            agent = self.name_to_agent[agent_name]
            state = agent.observe_as_dict()

            cartx = state["x"] * scale + screen_width / 2.0  # MIDDLE OF CART
            self.carttrans[agent_name].set_translation(cartx, carty)

        for agent_name, pole in self.poles.items():
            agent = self.name_to_agent[agent_name]
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

    name_to_agent: Mapping[AgentNameT, ExperimentalCartpoleAgent]

    def __init__(
        self, agents: Sequence[ExperimentalCartpoleAgent], port: str = "COM3", baudrate: int = 74880
    ) -> None:
        self.port = port
        self.baudrate = baudrate

        self.network_manager = NetworkManager(port=self.port, baudrate=self.baudrate)

        super().__init__(agents=agents)

    def _distribute_packet(self, packet: CartSpecificPacket) -> None:
        agent = self.cart_id_to_agent[packet.cart_id]

        agent.absorb_packet(packet)

    def _distribute_packets(self, packets: Sequence[CartSpecificPacket]) -> None:
        for packet in packets:
            self._distribute_packet(packet)

    def _process_buffer(self) -> None:
        """
        Call often to process packets in buffer of network manager.
        """
        # ObservationPackets
        obs_pkts = self.network_manager.get_packets(ObservationPacket, digest=False)
        self._distribute_packets(obs_pkts)

        # DebugPackets
        dbg_pkts = self.network_manager.get_packets(DebugPacket, digest=False)
        for dbg_pkt in dbg_pkts:
            logger.debug("CONTROLLER| %s", dbg_pkt.msg)

        # ErrorPackets
        err_pkts = self.network_manager.get_packets(ErrorPacket, digest=False)
        for err_pkt in err_pkts:
            logger.error("CONTROLLER| %s", err_pkt.msg)

    def setup(self) -> None:
        super().setup()

        self.cart_id_to_agent: dict[CartID, ExperimentalCartpoleAgent] = {}

        for agent_name in self.possible_agents:
            agent = self.name_to_agent[agent_name]

            agent.network_manager = self.network_manager
            self.cart_id_to_agent[agent.cart_id] = agent

        self.network_manager.open()
        self.network_manager.read_initial_output()

        assert not self.network_manager.in_queue

        # Check connection
        self.network_manager.assert_ping_pong()

        # Find limits
        find_limits_pkt = FindLimitsPacket()
        self.network_manager.send_packet(find_limits_pkt)

        # Wait for limit finding
        self.network_manager.get_packet(
            FindLimitsPacket, digest=True, block=True
        )

        # Flush InfoPackets
        self.network_manager.get_packets(
            InfoPacket, selector=message_startswith("LimitFinder: "), digest=False
        )
        assert not len(self.network_manager.packet_buffer)
        assert not self.network_manager.in_queue

        # Set velocity
        velo_pkt = SetVelocityPacket(SetOperation.EQUAL, cart_id=CartID.ONE, value=2000)
        self.network_manager.send_packet(velo_pkt)

    def reset(self) -> Mapping[str, ExternalState]:
        self.network_manager.serial.reset_input_buffer()

        self.agents = self.possible_agents[:]
        for agent in [self.name_to_agent[name] for name in self.agents]:
            agent._pre_reset()

        self.network_manager.assert_ping_pong()

        # Jiggle
        jiggle_pkt = DoJigglePacket()
        self.network_manager.send_packet(jiggle_pkt)
        self.network_manager.get_packet(DoJigglePacket, digest=True, block=True)

        # Ask controller to start experiment
        experiment_start_pkt = ExperimentStartPacket(0)
        self.network_manager.send_packet(experiment_start_pkt)

        while any([raises(self.name_to_agent[name].observe, IOError) for name in self.agents]):
            obs_pkts = self.network_manager.get_packets(
                ObservationPacket, digest=True, callback=self._process_buffer
            )
            self._distribute_packets(obs_pkts)

        return super().reset()

    def step(self, actions: dict[AgentNameT, Action]) -> StepReturn:
        # ! For now assume single cart. Change later
        # Very ugly temporary code - I'd like it to work today

        observations = {}
        rewards = {}
        dones = {}
        infos = {}

        for agent_name, action in actions.items():
            agent = self.name_to_agent[agent_name]

            infos[agent_name] = agent.step(action)

        self.network_manager.digest()
        self._process_buffer()

        # TODO Logic to wait for new observations here

        for agent in [self.name_to_agent[name] for name in self.agents]:
            observation = agent.observe()

            checks = agent.check_state(observation)
            done = any(checks.values())

            reward = agent.reward(observation) if not done else 0.0

            if done:
                failure_modes = [k.value for k, v in checks.items() if v]
                logger.info(f"Failure modes: {failure_modes}")

                infos[agent.name]["failure_modes"] = failure_modes

            info: StepInfo = {}

            observations[agent_name] = observation
            rewards[agent_name] = reward
            dones[agent_name] = done
            infos[agent_name] |= info

        # Flush packets for now
        self.network_manager.read_packets()

        self.steps += 1

        return observations, rewards, dones, infos


def make_env(base_env: Type[EnvT], *args: Any, num_frame_stacking: int = 1, **kwargs: Any) -> EnvT:
    env = base_env(*args, **kwargs)

    env = ss.frame_stack_v1(env, stack_size=num_frame_stacking)
    env = ss.black_death_v2(env)

    return env


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
