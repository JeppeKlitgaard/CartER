from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from time import time
from typing import Any, Generic, Optional, Type, TypedDict, cast

import gym
import supersuit as ss
from gym import spaces
from pettingzoo.utils.env import ParallelEnv

import deepmerge
from stable_baselines3.common.vec_env.vec_monitor import VecMonitor

from commander.experiment import ExperimentState
from commander.ml.agent import CartpoleAgent
from commander.ml.agent.agent import (
    CartpoleAgentT,
    ExperimentalCartpoleAgent,
    SimulatedCartpoleAgent,
)
from commander.ml.constants import Action
from commander.ml.display import rendering
from commander.network import NetworkManager
from commander.network.constants import (
    DEFAULT_BAUDRATE,
    DEFAULT_PORT,
    CartID,
    ExperimentInfoSpecifier,
    FailureMode,
    SetOperation,
)
from commander.network.protocol import (
    CartSpecificPacket,
    CheckLimitPacket,
    DebugPacket,
    DoJigglePacket,
    ErrorPacket,
    ExperimentDonePacket,
    ExperimentInfoPacket,
    ExperimentStartPacket,
    ExperimentStopPacket,
    FindLimitsPacket,
    InfoPacket,
    NullPacket,
    ObservationPacket,
    RequestDebugInfoPacket,
    SetMaxVelocityPacket,
    SetVelocityPacket,
    SoftLimitReachedPacket,
)
from commander.type_aliases import AgentNameT, ExternalState, StepInfo, StepReturn
from commander.utils import FrequencyTicker, raises

logger = logging.getLogger(__name__)


class EnvironmentState(TypedDict):
    experiment_state: Optional[ExperimentState]
    angle_drifts: dict[AgentNameT, float]
    position_drifts: dict[AgentNameT, int]
    failure_cart_id: CartID
    failure_agent: Optional[CartpoleAgent]
    failure_agent_name: Optional[AgentNameT]
    failure_mode: FailureMode
    track_length: Optional[int]
    last_observation_times: dict[AgentNameT, int]
    available_memory: Optional[int]


class CartpoleEnv(ParallelEnv, Generic[CartpoleAgentT]):  # type: ignore [misc]
    """
    Base Class for all Cartpole environments.
    """

    metadata = {
        "render.modes": ["human", "rgb_array"],
        "name": "Cartpole_v0",
    }

    def __init__(
        self,
        agents: Sequence[CartpoleAgentT],
        defer_reset: bool = True,
    ):
        self.agents = [agent.name for agent in agents]
        self.possible_agents = self.agents[:]
        self._agents = list(agents)

        self.name_to_agent: Mapping[AgentNameT, CartpoleAgentT] = dict(
            zip(self.possible_agents, self._agents)
        )

        self.action_spaces: Mapping[str, spaces.Space] = {
            agent.name: agent.action_space for agent in self.get_agents()
        }
        self.observation_spaces: Mapping[str, spaces.Space] = {
            agent.name: agent.observation_space for agent in self.get_agents()
        }

        self.seed()

        self.setup()

        # Note some key attributes are only set after calling reset!
        if not defer_reset:
            self.reset()

    def seed(self, seed: Optional[int] = None) -> list[Any]:
        seeds = [agent.seed() for agent in self.get_agents()]

        return seeds

    def setup(self) -> None:
        """
        Called when environment first initialised.

        Not called after each reset.
        """
        for agent in self.get_agents():
            agent.set_environment(self)

        self.episode: int = 0
        self.total_world_time: float = 0.0

        self.observation_freq_ticker = FrequencyTicker()

    def reset(self) -> Mapping[str, ExternalState]:
        self.episode += 1
        observations = {}

        # This needs to be agent names/ids
        self.agents = self.possible_agents[:]

        for agent in self.get_agents():
            observations[agent.name] = agent.reset()

        # ## Environment-level resets
        self.steps: int = 0
        self.viewer: Optional[rendering.Viewer] = None
        self.world_time: float = 0.0

        self.observation_freq_ticker.clear()

        # Return observations from agent reset
        return observations

    def observe(self, agent: str) -> ExternalState:
        return self.name_to_agent[agent].observe()

    def close(self) -> None:
        raise NotImplementedError("This should be overridden")

    def step(self, actions: dict[AgentNameT, Action]) -> StepReturn:
        """
        Performs a step using a dict of actions matching the current agents.
        """
        self.observation_freq_ticker.tick()

        result = self._step(actions=actions)
        return result

    def _step(self, actions: dict[AgentNameT, Action]) -> StepReturn:
        """
        Performs a step using a dict of actions matching the current agents.
        """
        raise NotImplementedError("This should be overriden")

    def get_agents(self, all_: bool = False) -> list[CartpoleAgentT]:
        """
        Returns a list of the current agents as agent objects.

        Use the `agents` attribute to get agent names.
        """
        agent_names = self.possible_agents if all_ else self.agents
        agents = [self.name_to_agent[name] for name in agent_names]

        return agents


EnvT = CartpoleEnv[CartpoleAgent]


class SimulatedCartpoleEnv(CartpoleEnv[SimulatedCartpoleAgent]):
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

        for agent in self.get_agents():
            assert isinstance(agent, SimulatedCartpoleAgent)

            agent.tau = self.timestep

    def _step(self, actions: dict[AgentNameT, Action]) -> StepReturn:
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
            observation_dict = agent.observe_as_dict()

            checks = agent.check_state(observation)
            done = any(checks.values())

            reward = agent.reward(observation) if not done else 0.0

            if done:
                failure_modes = [k.value for k, v in checks.items() if v]
                logger.info(f"Failure modes: {failure_modes}")

                info["failure_modes"] = failure_modes

            info["x"] = observation_dict["x"]
            info["theta"] = observation_dict["theta"]
            info["agent_name"] = agent.name
            info["environment_episode"] = self.episode
            info["world_time"] = self.world_time
            info["total_world_time"] = self.total_world_time
            info["observation_frequency"] = self.observation_freq_ticker.measure()

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
        if rendering is None:
            raise SystemError("Display not available. Cannot render.")

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
            for agent in self.get_agents():
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

                self.carts[agent.name] = cart
                self.carttrans[agent.name] = carttrans
                self.poles[agent.name] = pole
                self.poletrans[agent.name] = poletrans
                self.polelens[agent.name] = polelen
                self.axles[agent.name] = axle

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


class ExperimentalCartpoleEnv(CartpoleEnv[ExperimentalCartpoleAgent]):
    """
    An environment that represents the Cartpole Environment and
    implements networking with the physical experiment.
    """

    name_to_agent: Mapping[AgentNameT, ExperimentalCartpoleAgent]

    def __init__(
        self,
        agents: Sequence[ExperimentalCartpoleAgent],
        port: str = DEFAULT_PORT,
        baudrate: int = DEFAULT_BAUDRATE,
        observation_buffer_size: int = 100,
    ) -> None:
        self.port = port
        self.baudrate = baudrate

        self.observation_buffer_size = observation_buffer_size

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

        # NullPackets
        self.network_manager.get_packets(NullPacket, digest=False)

        # ObservationPackets
        obs_pkts = self.network_manager.get_packets(ObservationPacket, digest=False)
        self._distribute_packets(obs_pkts)

        # DebugPackets
        dbg_pkts = self.network_manager.get_packets(DebugPacket, digest=False)
        for dbg_pkt in dbg_pkts:
            logger.debug("CONTROLLER| %s", dbg_pkt.msg)

        # InfoPackets
        info_pkts = self.network_manager.get_packets(InfoPacket, digest=False)
        for info_pkt in info_pkts:
            logger.info("CONTROLLER| %s", info_pkt.msg)

        # ErrorPackets
        err_pkts = self.network_manager.get_packets(ErrorPacket, digest=False)
        for err_pkt in err_pkts:
            logger.error("CONTROLLER| %s", err_pkt.msg)

        # ExperimentInfoPackets
        exp_info_pkts = self.network_manager.get_packets(ExperimentInfoPacket, digest=False)
        for exp_info_pkt in exp_info_pkts:
            agent: Optional[ExperimentalCartpoleAgent]
            try:
                agent = self.cart_id_to_agent[exp_info_pkt.cart_id]
            except KeyError:
                agent = None

            if exp_info_pkt.specifier == ExperimentInfoSpecifier.POSITION_DRIFT:
                assert agent is not None

                self.environment_state["position_drifts"][agent.name] = cast(
                    int, exp_info_pkt.value
                )

            elif exp_info_pkt.specifier == ExperimentInfoSpecifier.FAILURE_MODE:
                assert agent is not None

                self.environment_state["failure_cart_id"] = exp_info_pkt.cart_id
                self.environment_state["failure_agent"] = agent
                self.environment_state["failure_agent_name"] = agent.name
                self.environment_state["failure_mode"] = cast(FailureMode, exp_info_pkt.value)

            elif exp_info_pkt.specifier == ExperimentInfoSpecifier.TRACK_LENGTH_STEPS:
                self.environment_state["track_length"] = cast(int, exp_info_pkt.value)

                for agent in self.get_agents():
                    agent.update_goal(
                        {"track_length": cast(int, self.environment_state["track_length"])}
                    )

            elif exp_info_pkt.specifier == ExperimentInfoSpecifier.AVAILABLE_MEMORY:
                self.environment_state["available_memory"] = cast(int, exp_info_pkt.value)

            else:
                raise ValueError(
                    "Environment does not know how to deal with specifier: "
                    + exp_info_pkt.specifier.name
                )

            # SoftLimitReachedPackets
            # Just ignore since we currently use ExperimentInfoPackets to determine done state
            self.network_manager.get_packets(SoftLimitReachedPacket, digest=False)

        if len(self.network_manager.packet_buffer) >= 3:
            logger.error(
                "Had packets in buffer after processing: %s", self.network_manager.packet_buffer
            )

    def _reset_environment_state(self) -> None:
        self.environment_state: EnvironmentState = {
            "experiment_state": None,
            "angle_drifts": {},
            "position_drifts": {},
            "failure_cart_id": CartID.NUL,
            "failure_agent": None,
            "failure_agent_name": None,
            "failure_mode": FailureMode.NUL,
            "track_length": None,
            "last_observation_times": {},
            "available_memory": None,
        }

        for agent in self.get_agents():
            self.environment_state["last_observation_times"][agent.name] = 0

    def setup(self) -> None:
        logger.info("Running experimental environment setup")

        self._reset_environment_state()
        self.environment_state["experiment_state"] = ExperimentState.STARTING

        super().setup()

        self.cart_id_to_agent: dict[CartID, ExperimentalCartpoleAgent] = {}

        for agent in self.get_agents(all_=True):
            agent.setup_by_environment(
                network_manager=self.network_manager,
                observation_buffer_size=self.observation_buffer_size,
            )

            self.cart_id_to_agent[agent.cart_id] = agent

        logger.info("Opening serial connection to controller")
        self.network_manager.open()
        logger.info("Reading inital output")
        initial_output = self.network_manager.read_initial_output(print_=True)
        logger.debug("Initial output: %s", initial_output)

        # assert not self.network_manager.in_queue

        # Check connection
        self.network_manager.assert_ping_pong()

        # Find limits
        logger.info("Finding limits")
        find_limits_pkt = FindLimitsPacket()
        self.network_manager.send_packet(find_limits_pkt)

        # Wait for limit finding
        self.network_manager.get_packet(
            FindLimitsPacket, digest=True, block=True, callback=self._process_buffer
        )

        self.network_tick()

        logger.info("Limits found")

        # Set velocity
        logger.info("Setting velocity to zero")
        velo_pkt = SetVelocityPacket(SetOperation.EQUAL, cart_id=CartID.ONE, value=0)
        self.network_manager.send_packet(velo_pkt)

        debug_info_pkt = RequestDebugInfoPacket()
        self.network_manager.send_packet(debug_info_pkt)

        # Flush DebugPackets
        self.network_manager.get_packets(
            RequestDebugInfoPacket, digest=True, block=True, callback=self._process_buffer
        )

        self.total_world_time: float = 0.0

        logger.info("Experimental environment setup done")

    def reset(self) -> Mapping[str, ExternalState]:
        logger.info("Resetting experimental environment")

        self.environment_state["experiment_state"] = ExperimentState.RESETTING

        self._reset_environment_state()

        self.agents = self.possible_agents[:]
        for agent in self.get_agents():
            agent._pre_reset()

        self.network_manager.assert_ping_pong()

        # Set max velocity
        logger.info("Setting max velocity")
        max_velo_pkt = SetMaxVelocityPacket(SetOperation.EQUAL, cart_id=CartID.ONE, value=10_000)
        self.network_manager.send_packet(max_velo_pkt)

        # Set velocity
        logger.info("Setting velocity")
        velo_pkt = SetVelocityPacket(SetOperation.EQUAL, cart_id=CartID.ONE, value=0)
        self.network_manager.send_packet(velo_pkt)

        # Ask controller to start experiment
        logger.info("Starting experiment")
        experiment_start_pkt = ExperimentStartPacket(0)
        self.network_manager.send_packet(experiment_start_pkt)
        self.network_manager.get_packet(
            ExperimentStartPacket, digest=True, block=True, callback=self._process_buffer
        )

        while any([raises(agent.observe, IOError) for agent in self.get_agents()]):
            obs_pkts = self.network_manager.get_packets(
                ObservationPacket, digest=True, callback=self._process_buffer
            )
            self._distribute_packets(obs_pkts)

        self.wait_for_settled()

        # Jiggle
        logger.info("Jiggling carts to zero angle")
        jiggle_pkt = DoJigglePacket()
        self.network_manager.send_packet(jiggle_pkt)
        self.network_manager.get_packet(
            DoJigglePacket, digest=True, block=True, callback=self._process_buffer
        )

        self.wait_for_settled()

        # Set zero angles
        logger.info("Zeroing angles")
        for agent in self.get_agents():
            agent.set_angle_offset()

        # Set velocity
        logger.info("Setting velocity")
        velo_pkt = SetVelocityPacket(SetOperation.EQUAL, cart_id=CartID.ONE, value=0)
        self.network_manager.send_packet(velo_pkt)

        self.world_time_start = time()

        reset_result = super().reset()

        self.environment_state["experiment_state"] = ExperimentState.RUNNING

        return reset_result

    def network_tick(self) -> None:
        self.network_manager.digest()
        self._process_buffer()

    def is_settled(self) -> bool:
        return all([agent.is_settled() for agent in self.get_agents()])

    def wait_for_settled(self) -> None:
        logger.debug("Waiting for system to settle")

        while not self.is_settled():
            self.network_tick()

        logger.debug("Experiment settled")

    def end_experiment(self) -> dict[str, Any]:
        self.environment_state["experiment_state"] = ExperimentState.ENDING

        self.total_world_time += self.world_time

        infos: dict[str, Any] = {}
        for agent in self.get_agents():
            infos[agent.name] = {}

        logger.info("Ending experiment")

        self.wait_for_settled()

        logger.info("Jiggling carts to find angle wander")
        jiggle_pkt = DoJigglePacket()
        self.network_manager.send_packet(jiggle_pkt)
        self.network_manager.get_packet(
            DoJigglePacket, digest=True, block=True, callback=self._process_buffer
        )

        self.wait_for_settled()

        # Gets angle wander for each cart
        for agent in self.get_agents():
            self.environment_state["angle_drifts"][agent.name] = agent.get_angle_drift()

        # Check limits
        logger.info("Checking limits")
        chk_pkt = CheckLimitPacket()
        self.network_manager.send_packet(chk_pkt)
        self.network_manager.get_packet(
            CheckLimitPacket, digest=True, block=True, callback=self._process_buffer
        )

        # Stop experiment
        logger.info("Stopping carts")
        stop_pkt = ExperimentStopPacket()
        self.network_manager.send_packet(stop_pkt)

        # Wait for stop ACK
        self.network_manager.get_packet(
            ExperimentStopPacket, digest=True, block=True, callback=self._process_buffer
        )

        # Wait for experiment to end
        self.network_manager.get_packet(
            ExperimentDonePacket, digest=True, block=True, callback=self._process_buffer
        )

        # Process final packets
        self.network_tick()

        for agent_name, angle_drift in self.environment_state["angle_drifts"].items():
            infos[agent_name]["angle_drift"] = angle_drift

        for agent_name, position_drift in self.environment_state["position_drifts"].items():
            infos[agent_name]["position_drift"] = position_drift

        infos["failure_cart_id"] = self.environment_state["failure_cart_id"]

        self.environment_state["experiment_state"] = ExperimentState.ENDED

        return infos

    def _step(self, actions: dict[AgentNameT, Action]) -> StepReturn:
        # ! For now assume single cart. Change later
        # Very ugly temporary code - I'd like it to work today

        observations = {}
        rewards = {}
        dones = {}
        infos = {}

        for agent_name, action in actions.items():
            agent = self.name_to_agent[agent_name]

            infos[agent_name] = agent.step(action)

        self.network_tick()

        # Check if we have failed
        if self.environment_state["failure_mode"] is not FailureMode.NUL:
            assert self.environment_state["failure_agent_name"] is not None

            infos[self.environment_state["failure_agent_name"]] = {
                "failure_modes": [self.environment_state["failure_mode"].describe()]
            }
            dones[self.environment_state["failure_agent_name"]] = True

        while True:
            all_observations_are_new = all(
                [
                    self.environment_state["last_observation_times"][agent.name]
                    != agent.last_observation_time
                    for agent in self.get_agents()
                ]
            )

            if all_observations_are_new:
                break

            self.network_tick()

        for agent in self.get_agents():
            info: StepInfo = {}

            observation = agent.observe()
            observation_dict = agent.observe_as_dict()

            self.environment_state["last_observation_times"][
                agent.name
            ] = agent.last_observation_time

            info["x"] = observation_dict["x"]
            info["theta"] = observation_dict["theta"]
            info["agent_name"] = agent.name
            info["environment_episode"] = self.episode
            info["available_memory"] = self.environment_state["available_memory"]

            checks = agent.check_state(observation)
            done = any(checks.values())

            reward = agent.reward(observation) if not done else 0.0

            world_time = time() - self.world_time_start
            info["world_time"] = world_time
            info["total_world_time"] = self.total_world_time
            info["observation_frequency"] = self.observation_freq_ticker.measure()
            info["serial_in_waiting"] = self.network_manager.serial.in_waiting

            if done:
                failure_modes = [k.value for k, v in checks.items() if v]
                logger.info(f"Failure modes: {failure_modes}")

                info["failure_modes"] = failure_modes

            observations[agent_name] = observation
            rewards[agent_name] = reward
            dones[agent_name] = done or bool(dones.get(agent_name))
            infos[agent_name] |= info

        self.steps += 1

        if any(dones.values()):
            end_experiment_infos = self.end_experiment()
            deepmerge.merge_or_raise.merge(infos, end_experiment_infos)

            # TODO
            logger.debug("Environment state: %s", self.environment_state)

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


def get_sb3_env_root_env(env: VecMonitor) -> EnvT:
    root_env = cast(Any, env).unwrapped.par_env.unwrapped.env

    return cast(EnvT, root_env)
