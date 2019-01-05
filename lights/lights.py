import time as t
import threading
from flask import Flask, render_template
from flask import request, redirect
from neopixel import *

import argparse
import signal
import sys
from random import randint



app = Flask(__name__)

def update(state):
    pass

@app.route('/')
def hello_world():
    global state
    if state:
        img="ON.png"
        for i in range(strip.numPixels()):
            strip.setPixelColor(i,colourful[i % len(colourful)])
        strip.show()         

    else:
        img="OFF.png"
        for i in range(strip.numPixels()):
            strip.setPixelColor(i,off[i % len(off)])
        strip.show()         

    return render_template('index.html', img_url=img)

@app.route('/DN')
def dn():
    global state
    state = not(state)
    print("DN")
    return redirect('/')

def start_app():
    app.run(host='0.0.0.0')


def signal_handler(signal, frame):
        colorWipe(strip, Color(0,0,0))
        sys.exit(0)

def opt_parse():
        parser = argparse.ArgumentParser()
        parser.add_argument('-c', action='store_true', help='clear the display on exit')
        args = parser.parse_args()
        if args.c:
                signal.signal(signal.SIGINT, signal_handler)








state = True


green = Color(24,0,0)
red = Color(0,35,0)
yellow = Color(15,32,0)
violet =Color(0,32,38)
orange = Color(15,53,0)
pink =Color(0,35,21)
turquoise = Color(15,0,9)
blue = Color(0,0,21) 
pinky_red = Color(0,47,6)
black = Color(0,0,0)



colourful = [turquoise,red,yellow,violet,orange,pink,green,blue,pinky_red]
off = [black]



# LED strip configuration:
LED_COUNT      = 200      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_GRB   # Strip type and colour ordering


if __name__ == "__main__":
    thread = threading.Thread(target=start_app, args=())
    thread.daemon = True                            # Daemonize thread
    thread.start()      

    opt_parse()

	# Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
	# Intialize the library (must be called once before other functions).
    strip.begin()
    print(strip.numPixels())
    signal.pause()
