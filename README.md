# Tree lights

A Raspberry Pi Pico W drives a string of 200 WS2811 LEDs. Tap the tree on a web page, or press BOOTSEL, to turn the lights on or off. A daily schedule can do it for you.

This replaces the original Raspberry Pi and Flask version, which is still in this repo's history. The colours and their order are the same as before.

![Board layout on the ProtoMate for Pico](docs/protomate-layout.png)

## Wiring

The string's input end connects to the Pico. The Pico passes USB power through to the lights.

| Pico | String |
|---|---|
| VBUS (pin 40) | 5V |
| GND (pin 38) | GND |
| GP0 (pin 1), through a 330–470 Ω resistor | DATA |

- Put a 1000 µF capacitor across 5V and GND, with the stripe to GND.
- Power the Pico from a 5V USB charger rated 2–3 A, not a laptop port.
- [docs/protomate-layout.png](docs/protomate-layout.png) shows a soldered build on a ProtoMate for Pico, with a 3-pin terminal for the string's pigtail.

## Install

1. Flash MicroPython (tested on 1.22.2) onto the Pico W.
2. Copy `wifi_config.example.py` to `wifi_config.py` and fill in your WiFi name and password. Git ignores this file.
3. Copy the files to the Pico:

```bash
mpremote cp main.py index.html manifest.json icon-192.png icon-512.png wifi_config.py :
```

4. Reset the Pico. It prints its address on the serial console; open `http://<pico-ip>/` on any device on the same network.

Reserve the Pico's IP address in your router so the address doesn't change. You can add the page to a phone's home screen.

## Files

| File | What it does |
|---|---|
| `main.py` | Lights, BOOTSEL button, schedule, WiFi, clock (UK time) and web server |
| `index.html` | The web page |
| `manifest.json`, `icon-*.png` | Home-screen icon |
| `wifi_config.example.py` | Template for your WiFi details |
| `treelights.json` | Saved on/off state and schedule, created on the Pico |

## Troubleshooting

- **Only the first LED lights up:** the Pico is connected to the string's output end. Use the other end.
- **Chrome on Android can't open the page, but other browsers can:** in Android settings, turn Chrome's Nearby devices permission off and on again, then force-stop Chrome.
