import serial
from timeit import default_timer as timer
from datetime import timedelta

PORT = "COM3"
BAUDRATE = 74880

s = serial.Serial(PORT, BAUDRATE)

