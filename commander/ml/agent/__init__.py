from typing import Any, Type

from commander.ml.agent.agent import (
    CartpoleAgent,
    SimulatedCartpoleAgent,
    ExperimentalCartpoleAgent,
)
from commander.ml.agent.goal import AgentGoalMixinBase, AgentTimeGoalMixin, AgentSwingupGoalMixin
from commander.ml.agent.state_specification import (
    AgentStateSpecificationBase,
    AgentTotalKnowledgeStateSpecification,
    AgentPositionalKnowledgeStateSpecification,
)


# Any to stop 'only concrete class can be given' mypy error.
# See: https://github.com/python/mypy/issues/5374
def make_agent(
    agent: Any,
    state_spec: Type[AgentStateSpecificationBase],
    goal: Type[AgentGoalMixinBase],
    *args,
    **kwargs,
) -> CartpoleAgent:
    class Agent(goal, state_spec, agent):
        ...

    return Agent(*args, **kwargs)


__all__ = (
    "make_agent",
    "CartpoleAgent",
    "SimulatedCartpoleAgent",
    "ExperimentalCartpoleAgent",
    "AgentGoalMixinBase",
    "AgentTimeGoalMixin",
    "AgentSwingupGoalMixin",
    "AgentStateSpecificationBase",
    "AgentTotalKnowledgeStateSpecification",
    "AgentPositionalKnowledgeStateSpecification",
)
