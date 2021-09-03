# Introducing CartER

CartER is a physical experimental setup for the development and exploration
of reinforcement learning algorithms in a reproducable, accessible way.

The [OpenAI Gym] and [PettingZoo] projects have provided a standardised set of environments
for use in single and multiagent reinforcement learning, which has 
enabled the academic community to use a consistent, reproducable environment
across different papers, research groups, and organisations.

CartER enables the user to try out reinforcement learning algorithms (mainly model-free ones)
on a physical system as well as a more involved cartpole environment than the one
found in the [OpenAI Gym].

## Why do we care about physical systems?

Physical systems are inherently noisy and introduce a variety of random and 
systematic errors that prove challenging for to accurately and reliably overcome using
traditional methods. Agents trained in such an environment, however, can be expected
to be more resillient towards errors in the observation and action spaces.

CartER could thus be a valuable tool for reinforcement learning researchers hoping to 
battle-test their algorithms in a physical environment where resillience against
latency and variable step intervals pose new challenges.

Further, a physical system imposes constraints on inference and learning times, as the
dynamics of the system will continue to act as the model is performing blocking operations.

As such, one might expect off-policy models may outperform on-policy models in this domain,
as inference and learning can more easily be separated, thus allowing for a tighter
action-observation loop separate to the learning routine.

## Why do we care about CartER?

CartER is open-source, cheap, and made of readily available parts. Thus, it lives up to many
of the requirements of a standard benchmark, which will be of significant importance as the field
of model-free reinforcement learning will start to more thoroughly explore viable implementations
in the area of physical systems. 

## Perspectives

Studying physical systems using reinforcement learning has a number of potentially profitable
perspectives.

### Symbolic Regression

Combined with symbolic regression/optimisation (cf. [DSO]) it may be possible to recover the equations of
motion for a given physical system. While the cartpole system is well-studied and the governing equations
already known, demonstrating symbolic regression using CartER could give confidence to projects hoping
to recover information from more complicated systems where traditional methods may be untenable or 
fail entirely.

Further, CartER could be used in a coupled two-carriage configuration to study symbolic regression
in multiagent environments or to demonstrate how reinforcement learning could be a faster, more robust way
to recover information about coupled mechanical systems.


[OpenAI Gym]: https://gym.openai.com/
[PettingZoo]: https://www.pettingzoo.ml/
[DSO]: https://github.com/brendenpetersen/deep-symbolic-optimization
