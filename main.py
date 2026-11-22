# treeLights for Raspberry Pi Pico W (MicroPython)
# Port of lights/lights.py from github.com/jrobinson-uk/treeLights.
#
# Wiring (5V string, pass-through power from USB):
#   Pico VBUS (pin 40) -> string V+
#   Pico GND  (pin 38) -> string GND
#   Pico GP0  (pin 1)  -> 330-470 ohm resistor -> string DATA (input end)
# Power the Pico from a 5V 2-3A USB charger, not a laptop port.
#
# Files on the Pico:
#   main.py          this program
#   index.html       the web page (tap the tree to toggle)
#   wifi_config.py   WIFI_SSID / WIFI_PASSWORD (falls back to config.py)
#   treelights.json  saved state and schedule (created automatically)
#
# Controls: the web page at http://<pico-ip>/ , or press BOOTSEL to toggle.

import json
import time

import machine
import neopixel
import network
import ntptime
import rp2
import uasyncio as asyncio

LED_COUNT = 200
DATA_PIN = 0
HOSTNAME = "treelights"
STATE_FILE = "treelights.json"

# Colours copied byte-for-byte from the repo. MicroPython's neopixel sends
# GRB order, same as the repo's WS2811_STRIP_GRB setting, so each tuple
# produces exactly the same pixel as the matching Color(...) in lights.py.
green = (24, 0, 0)
red = (0, 35, 0)
yellow = (15, 32, 0)
violet = (0, 32, 38)
orange = (15, 53, 0)
pink = (0, 35, 21)
turquoise = (15, 0, 9)
blue = (0, 0, 21)
pinky_red = (0, 47, 6)
black = (0, 0, 0)

colourful = [turquoise, red, yellow, violet, orange, pink, green, blue, pinky_red]
off = [black]

np = neopixel.NeoPixel(machine.Pin(DATA_PIN), LED_COUNT)
status_led = machine.Pin("LED", machine.Pin.OUT)
wlan = network.WLAN(network.STA_IF)

state = {"on": True, "schedule": {"enabled": False, "on": "16:00", "off": "23:00"}}
clock_ok = False


# ---------- lights and saved state ----------

def show(pattern):
    for i in range(LED_COUNT):
        np[i] = pattern[i % len(pattern)]
    np.write()


def apply_lights():
    show(colourful if state["on"] else off)
    status_led.value(1 if state["on"] else 0)


def load_state():
    try:
        with open(STATE_FILE) as f:
            saved = json.load(f)
        state["on"] = bool(saved.get("on", True))
        state["schedule"].update(saved.get("schedule", {}))
    except (OSError, ValueError):
        pass


def save_state():
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    except OSError as e:
        print("save failed:", e)


def set_on(on):
    if state["on"] != on:
        state["on"] = on
        apply_lights()
        save_state()


# ---------- UK time (GMT / BST) ----------

def _last_sunday(year, month):
    # day-of-month of the last Sunday; month has 31 days for March and October
    t = time.mktime((year, month, 31, 1, 0, 0, 0, 0))
    wday = time.localtime(t)[6]  # Monday=0 .. Sunday=6
    return 31 - ((wday + 1) % 7)


def uk_now():
    t = time.time()
    y = time.localtime(t)[0]
    bst_start = time.mktime((y, 3, _last_sunday(y, 3), 1, 0, 0, 0, 0))
    bst_end = time.mktime((y, 10, _last_sunday(y, 10), 1, 0, 0, 0, 0))
    if bst_start <= t < bst_end:
        t += 3600
    return time.localtime(t)


def hhmm(tm):
    return "%02d:%02d" % (tm[3], tm[4])


def next_event_text():
    sc = state["schedule"]
    if not sc["enabled"]:
        return "Schedule is off"
    if not clock_ok:
        return "Schedule waiting for the clock to set"
    now = hhmm(uk_now())

    def mins_until(t):
        return (int(t[:2]) * 60 + int(t[3:]) - int(now[:2]) * 60 - int(now[3:])) % 1440

    if mins_until(sc["on"]) <= mins_until(sc["off"]):
        return "Next: on at %s, every day" % sc["on"]
    return "Next: off at %s, every day" % sc["off"]


def public_state():
    return {
        "on": state["on"],
        "schedule": state["schedule"],
        "time": hhmm(uk_now()) if clock_ok else None,
        "next": next_event_text(),
    }


# ---------- background tasks ----------

async def button_task():
    while True:
        if rp2.bootsel_button():
            set_on(not state["on"])
            while rp2.bootsel_button():
                await asyncio.sleep_ms(10)
            await asyncio.sleep_ms(50)
        await asyncio.sleep_ms(30)


async def schedule_task():
    # Fires once when the clock reaches the on or off time. A manual change
    # in between stays until the next scheduled time.
    last = None
    while True:
        sc = state["schedule"]
        if clock_ok and sc["enabled"]:
            now = hhmm(uk_now())
            if now != last:
                if now == sc["on"]:
                    set_on(True)
                elif now == sc["off"]:
                    set_on(False)
                last = now
        await asyncio.sleep(5)


def wifi_credentials():
    try:
        import wifi_config as c
    except ImportError:
        import config as c  # reuse the existing config.py on this Pico
    return c.WIFI_SSID, c.WIFI_PASSWORD


async def network_task():
    global clock_ok
    network.hostname(HOSTNAME)
    wlan.active(True)
    wlan.config(pm=0xA11140)  # disable power saving so the page responds quickly
    try:
        ssid, password = wifi_credentials()
    except Exception:
        print("WiFi: no wifi_config.py or config.py, web page disabled")
        return
    last_sync = None
    while True:
        if not wlan.isconnected():
            print("WiFi: connecting to", ssid)
            wlan.connect(ssid, password)
            for _ in range(30):
                if wlan.isconnected():
                    break
                await asyncio.sleep(1)
            if wlan.isconnected():
                print("WiFi: connected, open http://%s/" % wlan.ifconfig()[0])
            else:
                print("WiFi: failed, retrying in 30s")
                wlan.disconnect()
        if wlan.isconnected() and (last_sync is None or time.ticks_diff(time.ticks_ms(), last_sync) > 6 * 3600 * 1000):
            try:
                ntptime.settime()
                clock_ok = True
                last_sync = time.ticks_ms()
                print("Clock set:", hhmm(uk_now()), "UK time")
            except Exception as e:
                print("Clock sync failed:", e)
        await asyncio.sleep(30)


# ---------- web server ----------

STATIC_FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/manifest.json": ("manifest.json", "application/manifest+json"),
    "/icon-192.png": ("icon-192.png", "image/png"),
    "/icon-512.png": ("icon-512.png", "image/png"),
}


def _send_json(writer, obj, status="200 OK"):
    body = json.dumps(obj)
    writer.write("HTTP/1.0 %s\r\nContent-Type: application/json\r\nCache-Control: no-store\r\nContent-Length: %d\r\nConnection: close\r\n\r\n" % (status, len(body)))
    writer.write(body)


async def _send_file(writer, path, ctype):
    writer.write("HTTP/1.0 200 OK\r\nContent-Type: %s\r\nConnection: close\r\n\r\n" % ctype)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(1024)
            if not chunk:
                break
            writer.write(chunk)
            await writer.drain()


def _valid_time(t):
    try:
        return len(t) == 5 and t[2] == ":" and 0 <= int(t[:2]) < 24 and 0 <= int(t[3:]) < 60
    except ValueError:
        return False


async def handle(reader, writer):
    try:
        peer = writer.get_extra_info("peername")[0]
    except Exception:
        peer = "?"
    print("connect:", peer)
    try:
        # Browsers open spare connections they may never use; drop idle ones
        # so they don't use up the Pico's small pool of sockets.
        line = await asyncio.wait_for(reader.readline(), 5)
        parts = line.decode().split()
        if len(parts) < 2:
            print("empty connection:", peer)
            return
        method, path = parts[0], parts[1].split("?")[0]
        print("request:", peer, method, path)
        length = 0
        while True:
            h = await asyncio.wait_for(reader.readline(), 5)
            if not h or h == b"\r\n":
                break
            if h.lower().startswith(b"content-length:"):
                length = int(h.split(b":")[1])
        body = {}
        if length:
            body = json.loads(await reader.readexactly(min(length, 1024)))

        if path == "/favicon.ico":
            path = "/icon-192.png"
        if method == "GET" and path in STATIC_FILES:
            name, ctype = STATIC_FILES[path]
            await _send_file(writer, name, ctype)
        elif path == "/api/state":
            if method == "POST" and "on" in body:
                set_on(bool(body["on"]))
            _send_json(writer, public_state())
        elif path == "/api/schedule" and method == "POST":
            sc = state["schedule"]
            if "enabled" in body:
                sc["enabled"] = bool(body["enabled"])
            for k in ("on", "off"):
                if k in body and _valid_time(body[k]):
                    sc[k] = body[k]
            save_state()
            _send_json(writer, public_state())
        else:
            _send_json(writer, {"error": "not found"}, "404 Not Found")
        await writer.drain()
    except Exception as e:
        print("request error:", e)
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


async def main():
    load_state()
    apply_lights()
    asyncio.create_task(button_task())
    asyncio.create_task(schedule_task())
    asyncio.create_task(network_task())
    await asyncio.start_server(handle, "0.0.0.0", 80)
    while True:
        await asyncio.sleep(3600)


asyncio.run(main())
