import numpy as np

import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from scipy.integrate import solve_ivp

from gym_ext.equations import derivatives_wrapper

plt.rcParams["figure.figsize"] = (16, 12)

F = 0
g = 9.8
m_c = 1.0
m_p = 0.1
M = m_c + m_p
l = 0.5
m_l = m_p * l
mu_c = 0.01
mu_p = 0.001

# @jit(**numba_options)
# def sgn(x: float) -> bool:
#     return (x > 0) - (x < 0)


t = np.linspace(0, 20, 1000000)


initial_conditions = [np.pi / 2, 0, 0, 0]

print("Solving...")
sol = solve_ivp(
    fun=derivatives_wrapper,
    t_span=[t[0], t[-1]],
    y0=initial_conditions,
    method="RK45",
    t_eval=t,
    args=(F, g, mu_c, mu_p, l, m_p, m_l, M),
)
print(sol)

fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)

ax1.plot(sol.t, sol.y[0])
ax1.yaxis.set_major_formatter(FormatStrFormatter(r"%g $\pi$"))
ax1.title.set_text("Angle")

ax2.plot(sol.t, sol.y[1])
ax2.yaxis.set_major_formatter(FormatStrFormatter(r"%g $\pi$"))
ax2.title.set_text("Angular Velocity")

ax3.plot(sol.t, sol.y[2])
ax3.title.set_text("Position")

ax4.plot(sol.t, sol.y[3])
ax4.title.set_text("Velocity")

plt.tight_layout()
plt.show()
