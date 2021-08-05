"""
Jordan Lei, 2020. Some code is based on the following sources:
   https://towardsdatascience.com/understanding-actor-critic-methods-931b97b6df3f
"""

import argparse
import os
import time

import numpy as np

import gym
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.autograd import Variable
from torch.distributions import Categorical
from torch.functional import Tensor
from torch.utils.tensorboard import SummaryWriter

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import seaborn as sns

from gym_ext import register_cartpole
from gym_ext.cartpole import CartPoleEnv
from gym_ext.typing import State

parser = argparse.ArgumentParser()
parser.add_argument("--device", type=int, default=0)  # cuda device
parser.add_argument("--verbose", type=int, default=1)  # printing preferences
parser.add_argument("--load", type=bool, default=False)  # if loading an existing model
parser.add_argument("--save", type=bool, default=False)  # if saving an existing model
parser.add_argument("--plot", type=bool, default=True)  # if plotting an existing model
parser.add_argument(
    "--model", type=str, default="reinforce_cartpole/model.pt"
)  # model - currently supports resnet and alexnet, with more to come
parser.add_argument(
    "--runtype", type=str, default="train_run", choices=("train", "run", "train_run")
)  # runtype: train only or train and validate
parser.add_argument("--lr", type=float, default=0.01)  # learning rate
parser.add_argument("--episodes", type=int, default=500)  # number of episodes
parser.add_argument("--gamma", type=float, default=0.99)  # discount factor
args = parser.parse_args()

# setup environment
register_cartpole(max_episode_steps=1000)
wrapped_env = gym.make("CartPole-v2", force_mag=8.0, friction_cart=0.1, friction_pole=0.5)

env = wrapped_env.unwrapped

MAX_RUN_EPISODES = 25000

# set the cuda visible devices
os.environ["CUDA_VISIBLE_DEVICES"] = "{}".format(args.device)
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


# actor network
class Actor(nn.Module):
    def __init__(self, in_size: int, out_size: int):
        super().__init__()
        self.linear1 = nn.Linear(in_size, 128)
        self.linear2 = nn.Linear(128, out_size)
        self.dropout = nn.Dropout(0.7)
        self.softmax = nn.Softmax(dim=1)

        self.policy_history = Variable(torch.Tensor()).to(device)
        self.reward_episode = []

        self.reward_history = []
        self.loss_history = []

    def forward(self, x: Tensor) -> Tensor:
        # convert numpy state to tensor
        x = Variable(torch.from_numpy(x).float().unsqueeze(0)).to(device)
        x = F.relu(self.linear1(x))
        x = self.dropout(x)
        x = self.softmax(self.linear2(x))
        return x


# critic network
class Critic(nn.Module):
    def __init__(self, in_size: int):
        super().__init__()
        self.linear1 = nn.Linear(in_size, 128)
        self.linear2 = nn.Linear(128, 1)
        self.dropout = nn.Dropout(0.7)

        self.value_episode = []
        self.value_history = Variable(torch.Tensor()).to(device)

    def forward(self, x: Tensor) -> Tensor:
        x = Variable(torch.from_numpy(x).float().unsqueeze(0)).to(device)
        x = F.relu(self.linear1(x))
        x = self.linear2(x)
        return x


# combined module (mostly for loading / storing)
class ActorCritic(nn.Module):
    def __init__(self, actor: Actor, critic: Critic):
        super(ActorCritic, self).__init__()
        self.actor = actor
        self.critic = critic

    def forward(self, x: Tensor) -> tuple[Tensor, Tensor]:
        value = self.critic(x)
        policy = self.actor(x)

        return value, policy


class Runner:
    def __init__(
        self,
        actor: Actor,
        critic: Critic,
        a_optimizer: optim.Optimizer,
        c_optimizer: optim.Optimizer,
        gamma: float = 0.99,
        logs: str = "a2c_cartpole",
    ):
        self.actor = actor
        self.critic = critic
        self.a_opt = a_optimizer
        self.c_opt = c_optimizer
        self.gamma = gamma
        self.logs = logs
        self.writer = SummaryWriter(logs)
        self.entropy = 0
        self.plots = {"Actor Loss": [], "Critic Loss": [], "Reward": [], "Mean Reward": []}

    def env_step(self, action):
        state, reward, done, log = env.step(action)
        return (
            torch.FloatTensor([state]).to(device),
            torch.FloatTensor([reward]).to(device),
            done,
            log,
        )

    def select_action(self, state: State):
        # convert state to tensor
        probs = self.actor(state)
        c = Categorical(probs)
        action = c.sample()

        # place log probabilities into the policy history log\pi(a | s)
        if self.actor.policy_history.dim() != 0:
            self.actor.policy_history = torch.cat([self.actor.policy_history, c.log_prob(action)])
        else:
            self.actor.policy_history = c.log_prob(action)

        return action

    def estimate_value(self, state):
        pred = self.critic(state).squeeze(0)
        if self.critic.value_history.dim() != 0:
            self.critic.value_history = torch.cat([self.critic.value_history, pred])
        else:
            self.critic.policy_history = pred

    def update_a2c(self):
        R = 0
        q_vals = []

        # "unroll" the rewards, apply gamma
        for r in self.actor.reward_episode[::-1]:
            R = r + self.gamma * R
            q_vals.insert(0, R)

        q_vals_ft = torch.FloatTensor(q_vals).to(device)
        values = self.critic.value_history
        log_probs = self.actor.policy_history

        # print(values)
        # print(log_probs)
        advantage = q_vals_ft - values

        self.c_opt.zero_grad()
        critic_loss = 0.0005 * advantage.pow(2).mean()
        critic_loss.backward()
        self.c_opt.step()

        self.a_opt.zero_grad()
        actor_loss = (-log_probs * advantage.detach()).mean() + 0.001 * self.entropy
        actor_loss.backward()
        self.a_opt.step()

        self.actor.reward_episode = []
        self.actor.policy_history = Variable(torch.Tensor()).to(device)
        self.critic.value_history = Variable(torch.Tensor()).to(device)

        return actor_loss, critic_loss

    def train(self, episodes: int = 200, smooth: int = 10) -> None:
        smoothed_reward = []

        for episode in range(episodes):
            rewards = 0.0
            state = env.reset()
            self.entropy = 0
            done = False

            for step in range(env.spec.max_episode_steps):
                self.estimate_value(state)

                policy = self.actor(state).cpu().detach().numpy()
                action = self.select_action(state)

                e = -np.sum(np.mean(policy) * np.log(policy))
                self.entropy += e

                state, reward, done, _ = env.step(action.data[0].item())
                rewards += reward

                self.actor.reward_episode.append(reward)

                if done:
                    break

            smoothed_reward.append(rewards)
            if len(smoothed_reward) > smooth:
                smoothed_reward = smoothed_reward[-1 * smooth : -1]

            a_loss, c_loss = self.update_a2c()

            self.writer.add_scalar("Critic Loss", c_loss, episode)
            self.writer.add_scalar("Actor Loss", a_loss, episode)
            self.writer.add_scalar("Reward", rewards, episode)
            self.writer.add_scalar("Mean Reward", np.mean(smoothed_reward), episode)

            self.plots["Critic Loss"].append(c_loss * 100)
            self.plots["Actor Loss"].append(a_loss)
            self.plots["Reward"].append(rewards)
            self.plots["Mean Reward"].append(np.mean(smoothed_reward))

            if episode % 20 == 0:
                print(
                    "\tEpisode {} \t Final Reward {:.2f} \t Average Reward: {:.2f}".format(
                        episode, rewards, np.mean(smoothed_reward)
                    )
                )

    def run(self) -> None:
        sns.set_style("dark")
        sns.set_context("poster")

        fig = plt.figure()
        ims = []
        rewards = 0.0
        state = env.reset()
        for i in range(MAX_RUN_EPISODES):
            action = self.select_action(state)
            state, reward, done, _ = env.step(action.data[0].item())
            rewards += reward

            if done:
                break

            im = plt.imshow(env.render(mode="rgb_array"), animated=True)
            plt.axis("off")
            plt.title("Actor Critic Agent")
            ims.append([im])

        print("\tTotal Reward: ", rewards)
        env.close()
        print("\tSaving Animation ...")
        ani = animation.ArtistAnimation(fig, ims, interval=20, blit=True, repeat_delay=1000)
        ani.save("%s-movie.avi" % self.logs, dpi=300)

    def save(self) -> None:
        ac = ActorCritic(self.actor, self.critic)
        torch.save(ac.state_dict(), "%s/model.pt" % self.logs)

    def plot(self) -> None:
        sns.set()
        sns.set_context("poster")

        plt.figure(figsize=(20, 16))

        actor_losses = [loss.detach().numpy() for loss in self.plots["Actor Loss"]]
        critic_losses = [loss.detach().numpy() for loss in self.plots["Critic Loss"]]

        plt.plot(np.arange(len(actor_losses)), actor_losses, label="Actor")
        plt.plot(np.arange(len(critic_losses)), critic_losses, label="Critic (x100)")
        plt.legend()
        plt.title("A2C Loss")
        plt.xlabel("Episodes")
        plt.ylabel("Loss")
        plt.savefig("%s/plot_%s.png" % (self.logs, "loss"))

        plt.figure(figsize=(20, 16))
        plt.plot(np.arange(len(self.plots["Reward"])), self.plots["Reward"], label="Reward")
        plt.plot(
            np.arange(len(self.plots["Mean Reward"])),
            self.plots["Mean Reward"],
            label="Mean Reward",
        )
        plt.legend()
        plt.title("A2C Rewards")
        plt.xlabel("Episodes")
        plt.ylabel("Rewards")
        plt.savefig("%s/plot_%s.png" % (self.logs, "rewards"))


def main() -> None:
    device_name = "cuda: %s" % (args.device) if torch.cuda.is_available() else "cpu"
    print("[Device]\tDevice selected: ", device_name)

    actor = Actor(env.observation_space.shape[0], env.action_space.n).to(device)
    critic = Critic(env.observation_space.shape[0]).to(device)
    ac = ActorCritic(actor, critic)

    # if we're loading a model
    if args.load:
        ac.load_state_dict(torch.load(args.model))
        actor = ac.actor
        critic = ac.critic

    a_optimizer = optim.Adam(actor.parameters(), lr=args.lr)
    c_optimizer = optim.Adam(critic.parameters(), lr=args.lr)

    runner = Runner(actor, critic, a_optimizer, c_optimizer, logs="a2c_cartpole/%s" % time.time())

    if "train" in args.runtype:
        print("[Train]\tTraining Beginning ...")
        runner.train(args.episodes)

        if args.plot:
            print("[Plot]\tPlotting Training Curves ...")
            runner.plot()

    if args.save:
        print("[Save]\tSaving Model ...")
        runner.save()

    if "run" in args.runtype:
        print("[Run]\tRunning Simulation ...")
        runner.run()

    print("[End]\tDone. Congratulations!")


if __name__ == "__main__":
    main()
