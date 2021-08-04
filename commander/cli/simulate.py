import click
import time

from commander.ml.agent import SimulatedCartpoleAgent
from commander.ml.environment import make_sb3_env, make_env
import stable_baselines3

import supersuit as ss

from enum import Enum

SAVE_NAME_BASE: str = "cartpoleml_simulation_"


class Algorithm(str, Enum):
    # Note: Not all of these actually work with our action space and multiple agents
    # Known working: A2C, PPO
    A2C = "A2C"
    DDPG = "DDPG"
    DQN = "DQN"
    HER = "HER"
    PPO = "PPO"
    SAC = "SAC"
    TD3 = "TD3"


class Configuration(str, Enum):
    TWO_CARTS = "TWO_CARTS"
    ONE_CART = "ONE_CART"


@click.command()
@click.option("--train/--no-train", default=True)
@click.option("--render/--no-render", default=True)
@click.option("-t", "--total-timesteps", type=int, default=100000)
@click.option(
    "-c",
    "--configuration",
    type=click.Choice([_.value for _ in Configuration], case_sensitive=False),
    default=Configuration.TWO_CARTS,
)
@click.option(
    "-a",
    "--algorithm",
    type=click.Choice([_.value for _ in Algorithm], case_sensitive=False),
    default=Algorithm.PPO,
)
def simulate(train: bool, render: bool, total_timesteps: int, configuration: str, algorithm: str):
    agent_1 = SimulatedCartpoleAgent(name="Cartpole_1", start_pos=-1)
    agent_2 = SimulatedCartpoleAgent(name="Cartpole_2", start_pos=1, length=0.75)

    if configuration == Configuration.TWO_CARTS:
        agents = [agent_1, agent_2]
    elif configuration == Configuration.ONE_CART:
        agents = [agent_1]

    save_name = SAVE_NAME_BASE + algorithm
    algorithm_obj = getattr(stable_baselines3, algorithm)

    env = make_sb3_env(agents=agents)

    if train:
        model = algorithm_obj("MlpPolicy", env, verbose=1)
        model.learn(total_timesteps=total_timesteps)
        model.save(save_name)

    if render:
        env = make_env(agents=agents)
        model = algorithm_obj.load("baselines_a2c_test")

        obs = env.reset()
        for agent in env.agent_iter():
            obs, reward, done, info = env.last()

            action, state = model.predict(obs, deterministic=True) if not done else (None, None)

            env.step(action)
            env.render()

            if done:
                time.sleep(3)

                env.close()
                obs = env.reset()
