"""Light string test: run on any Pico with MicroPython (no app needed).

Data on GP0. Loops forever: all red, all green, all blue (dim), then one
white light running along the first 50. Copy to the Pico as main.py to run
it on power-up, or run it with:  mpremote run tools/lights_test.py
"""

import time

import machine
import neopixel

DATA_PIN = 0
COUNT = 200
LEVEL = 40          # 0-255, kept low so USB power and breadboards cope

np = neopixel.NeoPixel(machine.Pin(DATA_PIN), COUNT)
led = machine.Pin("LED", machine.Pin.OUT)

while True:
    for name, colour in (("red", (LEVEL, 0, 0)), ("green", (0, LEVEL, 0)), ("blue", (0, 0, LEVEL))):
        print("all", name)
        np.fill(colour)
        np.write()
        led.toggle()
        time.sleep(1.5)
    print("running light")
    for i in range(50):
        np.fill((0, 0, 0))
        np[i] = (LEVEL, LEVEL, LEVEL)
        np.write()
        time.sleep(0.05)
