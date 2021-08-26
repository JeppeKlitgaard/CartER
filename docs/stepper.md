# Steppers

Having the appropriate _pulse rate_ is critical when driving the steppers in a
`dir/step` mode. From the datasheet of, for example, the [RS PRO 5350479] stepper
motor, we can see that a pulse rate of $≈ 5\ \text{kHz}$ would be ideal 
if torque is the main concern.

In order to achieve a reliable pulse rate, we can utilise __timer interrupts__,
which is done using the `tc_lib` library for Arduino SAM. If you use a different board,
you may need to use a different library or implement the timer interrupts _by hand_.

Thus we which to have a timer period of:

$$
T = f^{-1} = \frac{1}{5000} = 2 ⋅ 10^{-4} s = 2 ⋅ 10^{4} \ \qty[10^{-8}\, s]
$$

[RS PRO 5350479]: https://docs.rs-online.com/3547/0900766b8157a732.pdf
