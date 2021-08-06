"""
Contains the differential equations governing a cartpole physics system.

The system is modelled using a few assumptions:
- The pole is rigid
- Forces are applied ∥ to the track
- Cart is only free to move in one dimension
- Friction between cart and track is given by μ_c, which is taken to be constant
- Friction in the joint between the cart and the pole is given by μ_p, also constant
- The pole is of uniform density

Changes to make in the future:
- Additional weight placed at a particular point on the pole

Note that the second order ODEs have been split into two first order ODEs each.
This is to facilitate numerical integration using `scipy.integrate.solve_ivp`.

See supporting document for pretty rendered math and explanations of
symbols.
"""

import logging
from typing import Any

from numpy import cos
from numpy import sign as sgn
from numpy import sin

from numba import jit

from commander.type_aliases import State

logger = logging.getLogger(__name__)

_NUMBA_OPTIONS = {
    "nopython": True,
    "nogil": True,
}

Params = tuple[float, Any, float, Any]

last_N_c: float


@jit(**_NUMBA_OPTIONS)  # type: ignore
def N_c(g: float, M: float, m_l: float, theta: float, thetadot: float, thetaddot: float) -> float:
    """
    Normal force of the cart.
    """
    return g * M - m_l * (thetaddot * sin(theta) + thetadot ** 2 * cos(theta))  # type: ignore


# Could probably speed this up by introducing a function
# builder and storing constants in scope instead of as args.
@jit(**_NUMBA_OPTIONS)  # type: ignore
def derivatives(
    t: float,
    y: State,
    last_N_c: float,
    F: float,
    g: float,
    mu_c: float,
    mu_p: float,
    l: float,
    m_p: float,
    m_l: float,
    M: float,
) -> tuple[Params, float]:
    """
    Returns a list of partial derivatives for `scipy.integrate.solve_ivp`

    Args:
        t: time
        y: vector of variables
    """

    # Setup variables from y
    x = y[0]  # x  # noqa
    b = y[1]  # dx/dt
    q = y[2]  # θ
    a = y[3]  # dθ/dt

    alpha = mu_c * sgn(last_N_c * b)

    # fmt: off
    adot = (
        (
            g * sin(q)
            + cos(q) * (  # noqa
                (
                    -F - m_l * a**2 * (sin(q) + alpha * cos(q))
                )
                / M  # noqa
                + g * alpha  # noqa
            )
            - mu_p * a / m_l  # noqa
        )
        /  # noqa
        (
            l * (
                4 / 3
                - (m_p * cos(q) / M) * (  # noqa
                    cos(q) - alpha
                )
            )
        )
    )
    # fmt: on

    new_N_c = N_c(g, M, m_l, q, a, adot)

    bdot = ((F + m_l * (a ** 2 * sin(q) - adot * cos(q))) - new_N_c * alpha) / M

    derivs = (
        b,
        bdot,
        a,
        adot,
    )

    return (derivs, new_N_c)


class DerivativesWrapper:
    """
    Wraps the derivatives function.

    We need to have the derivatives function be static in order to JIT compile it,
    but we also need context on whether the sign of the normal force on the
    cart has changed.

    This wrapper solves that by providing a context attribute, but leaving most
    of the computation in the static function.

    The derivatives function could also be implemented as a static method.
    """

    last_N_c: float

    def __init__(self):
        self.reset()

    def reset(self) -> None:
        self.last_N_c = 0.0

    def equation(
        self,
        t: float,
        y: Params,
        F: float,
        g: float,
        mu_c: float,
        mu_p: float,
        l: float,
        m_p: float,
        m_l: float,
        M: float,
    ) -> Params:

        derivs, new_N_c = derivatives(t, y, self.last_N_c, F, g, mu_c, mu_p, l, m_p, m_l, M)

        # Note: we should strictly check whether sign of N_c has changed and
        # recalculate using new N_c if this is the case.
        # For most sensible parameters N_c will never change sign, so we ignore
        # this for now, since it adds a significant slowdown.

        should_redo = sgn(self.last_N_c) != sgn(new_N_c) and self.last_N_c != 0
        # # We have changed sign of N_c, so we should recalculate adot based on the new sign

        self.last_N_c = new_N_c

        if should_redo:
            logger.info(
                "Normal force of cart changed sign, which requires recalculation. "
                "If you are getting this a lot or see recursion errors, you probably want "
                "to introduce more cart mass, as currently the experiment does not "
                "support flying carts anyway."
                )
            return self.equation(t, y, F, g, mu_c, mu_p, l, m_p, m_l, M)

        return derivs  # type: ignore
