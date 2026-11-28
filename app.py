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
#   main.py          small loader: runs app.py, rolls back a bad update
#   app.py           this program
#   index.html       the web page (tap the tree to toggle)
#   update.html      page for uploading new files over WiFi
#   wifi_config.py   WIFI_SSID / WIFI_PASSWORD (falls back to config.py)
#   treelights.json  saved state and schedule (created automatically)
#
# Controls: the web page at http://<pico-ip>/ , or press BOOTSEL to toggle.

import binascii
import gc
import hashlib
import json
import os
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

# Brightness is a percentage of the repo's original colours: 100 = as before.
# Every channel is scaled by the same factor, so each colour keeps its tone.
# The cap keeps the string's current within what a 2-3A USB charger can feed
# through the Pico (about 0.7A at 100%, about 1.75A at 250%).
BRIGHTNESS_MIN = 20
BRIGHTNESS_MAX = 250

# Custom colours from the web page are stored as [red, green, blue], as you
# see them, at 100% brightness. None means the repo's colours above.
MAX_COLOURS = 24
# Power limit: average (red+green+blue) across the pattern x brightness %.
# The repo's colours average 44.2, so 11100 allows them up to 250% (about
# 1.75A). Brighter custom colours lower the top of the brightness slider.
POWER_BUDGET = 11100

state = {"on": True, "brightness": 100, "colours": None, "locked": False,
         "schedule": {"enabled": False, "on": "16:00", "off": "23:00"}}
clock_ok = False


# ---------- lights and saved state ----------

def scaled(colour, pct):
    return tuple(min(255, (c * pct + 50) // 100) for c in colour)


def pattern():
    """The colour pattern as neopixel tuples (this string's tuple order is G, R, B)."""
    cs = state["colours"]
    return [(c[1], c[0], c[2]) for c in cs] if cs else colourful


def as_seen(t):
    return [t[1], t[0], t[2]]


def brightness_max():
    p = pattern()
    avg = sum(sum(c) for c in p) / len(p)
    if avg <= 0:
        return BRIGHTNESS_MAX
    return max(BRIGHTNESS_MIN, min(BRIGHTNESS_MAX, int(POWER_BUDGET / avg)))


def shown_brightness():
    # The saved brightness, lowered if the colours need it to stay in budget.
    return min(state["brightness"], brightness_max())


def show(pat):
    pct = shown_brightness()
    pat = [scaled(c, pct) for c in pat]
    for i in range(LED_COUNT):
        np[i] = pat[i % len(pat)]
    np.write()


def apply_lights():
    show(pattern() if state["on"] else off)
    status_led.value(1 if state["on"] else 0)


def load_state():
    try:
        with open(STATE_FILE) as f:
            saved = json.load(f)
        state["on"] = bool(saved.get("on", True))
        state["locked"] = bool(saved.get("locked", False))
        if check_colours(saved.get("colours")) is None:
            state["colours"] = saved["colours"]
        state["brightness"] = clamp_brightness(saved.get("brightness", 100))
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


def set_locked(locked):
    if state["locked"] != locked:
        state["locked"] = locked
        save_state()


def clamp_brightness(b, default=100):
    try:
        return max(BRIGHTNESS_MIN, min(BRIGHTNESS_MAX, int(b)))
    except (TypeError, ValueError):
        return default


def set_brightness(b):
    b = min(clamp_brightness(b, state["brightness"]), brightness_max())
    if state["brightness"] != b:
        state["brightness"] = b
        if state["on"]:
            show(pattern())
        save_state()


def check_colours(cs):
    """Return an error message, or None if cs is a usable colour list."""
    if not isinstance(cs, list) or not 1 <= len(cs) <= MAX_COLOURS:
        return "need 1 to %d colours" % MAX_COLOURS
    for c in cs:
        if not (isinstance(c, list) and len(c) == 3 and
                all(isinstance(v, int) and 0 <= v <= 255 for v in c)):
            return "each colour must be [red, green, blue], 0 to 255"
    if sum(sum(c) for c in cs) / len(cs) * BRIGHTNESS_MIN > POWER_BUDGET:
        return "those colours are too bright for the power supply"
    return None


def set_colours(cs):
    """cs is a list of [r, g, b] as seen, or None for the repo's colours."""
    if cs is not None:
        err = check_colours(cs)
        if err:
            return err
        if [(c[1], c[0], c[2]) for c in cs] == colourful:
            cs = None
    state["colours"] = cs
    if state["on"]:
        show(pattern())
    save_state()
    return None


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
        "locked": state["locked"],
        "brightness": shown_brightness(),
        "brightness_range": [BRIGHTNESS_MIN, brightness_max()],
        "colours": [as_seen(c) for c in pattern()],
        "colours_custom": state["colours"] is not None,
        "max_colours": MAX_COLOURS,
        "schedule": state["schedule"],
        "time": hhmm(uk_now()) if clock_ok else None,
        "next": next_event_text(),
    }


# ---------- background tasks ----------

async def button_task():
    while True:
        if rp2.bootsel_button():
            if state["locked"]:
                # Locked from the app: leave the lights alone, blink the
                # Pico's LED twice so it's clearly locked rather than broken.
                for _ in range(2):
                    status_led.value(0 if state["on"] else 1)
                    await asyncio.sleep_ms(150)
                    status_led.value(1 if state["on"] else 0)
                    await asyncio.sleep_ms(150)
            else:
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
    "/update": ("update.html", "text/html; charset=utf-8"),
}

# Files that can be replaced over WiFi. main.py (the loader) and the WiFi
# details are left out on purpose: those need USB.
UPLOADABLE = ("app.py", "index.html", "update.html", "manifest.json",
              "icon-192.png", "icon-512.png")
UPLOAD_MAX = 100 * 1024
PENDING_FILE = "update_pending"


def _exists(name):
    try:
        os.stat(name)
        return True
    except OSError:
        return False


def _remove(name):
    try:
        os.remove(name)
    except OSError:
        pass


def _free_bytes():
    s = os.statvfs("/")
    return s[0] * s[3]


async def _discard(reader, length):
    # Read and drop a body we're refusing; otherwise the connection resets
    # and the browser never sees the error message.
    left = min(length, 2 * UPLOAD_MAX)
    try:
        while left > 0:
            chunk = await asyncio.wait_for(reader.read(min(1024, left)), 5)
            if not chunk:
                break
            left -= len(chunk)
    except Exception:
        pass


async def _receive_upload(reader, name, length):
    # Stream the body to <name>.new, check it, then swap it in.
    refusal = None
    if name not in UPLOADABLE:
        refusal = "404 Not Found", "can't upload " + name
    elif not 0 < length <= UPLOAD_MAX:
        refusal = "400 Bad Request", "file must be 1 byte to %d KB" % (UPLOAD_MAX // 1024)
    elif length + 16 * 1024 > _free_bytes():
        refusal = "507 Insufficient Storage", "not enough space on the Pico"
    if refusal:
        await _discard(reader, length)
        return refusal
    tmp = name + ".new"
    got = 0
    with open(tmp, "wb") as f:
        while got < length:
            chunk = await asyncio.wait_for(reader.read(min(1024, length - got)), 10)
            if not chunk:
                break
            f.write(chunk)
            got += len(chunk)
    if got != length:
        _remove(tmp)
        return "400 Bad Request", "upload cut short"
    err = _syntax_error(tmp, name)
    if err:
        _remove(tmp)
        return "400 Bad Request", err
    _swap_in(tmp, name)
    return "200 OK", "saved %s (%d bytes)" % (name, got)


def _syntax_error(tmp, name):
    """Compile a downloaded .py file; return an error message, or None if it's fine."""
    if not name.endswith(".py"):
        return None
    gc.collect()
    try:
        with open(tmp) as f:
            compile(f.read(), name, "exec")
    except SyntaxError as e:
        return "syntax error in %s: %s" % (name, e)
    except MemoryError:
        pass  # too big to check here; the loader still rolls back if it fails
    finally:
        gc.collect()
    return None


def _swap_in(tmp, name):
    """Replace name with tmp. A new app.py goes on trial until it's run for 30s."""
    if name == "app.py" and _exists(name):
        # Keep the running version so the loader can roll back after restart.
        _remove("app.bak")
        os.rename(name, "app.bak")
        open(PENDING_FILE, "w").close()
    else:
        _remove(name)
    os.rename(tmp, name)
    _remove("app_error.txt")
    print("updated:", name)


# ---------- updates from GitHub ----------
# The Pico installs the release tagged "stable" in the repo, never master.
# release.json at that tag lists each file's size and SHA-256; files that
# differ from it are downloaded, checked, then swapped in together.

GITHUB_REPO = "jrobinson-uk/treeLights"
GITHUB_REF = "stable"


def _sha256_file(name):
    h = hashlib.sha256()
    try:
        with open(name, "rb") as f:
            while True:
                b = f.read(1024)
                if not b:
                    break
                h.update(b)
    except OSError:
        return None
    return binascii.hexlify(h.digest()).decode()


def _http_get(url, accept=None):
    import requests  # loaded only when needed: TLS uses a lot of memory
    gc.collect()
    headers = {"User-Agent": "treelights-pico"}
    if accept:
        headers["Accept"] = accept
    r = requests.get(url, headers=headers, timeout=20)
    if r.status_code != 200:
        r.close()
        raise OSError("GitHub returned %d for %s" % (r.status_code, url))
    return r


def _stable_release():
    """Return (commit sha, release manifest) for the stable tag."""
    r = _http_get("https://api.github.com/repos/%s/commits/%s" % (GITHUB_REPO, GITHUB_REF),
                  "application/vnd.github.sha")
    sha = r.text.strip()
    r.close()
    if len(sha) != 40:
        raise OSError("couldn't find the stable tag")
    r = _http_get("https://raw.githubusercontent.com/%s/%s/release.json" % (GITHUB_REPO, sha))
    manifest = r.json()
    r.close()
    return sha, manifest


def _compare(manifest):
    changed, usb_only = [], []
    for f in manifest["files"]:
        if _sha256_file(f["name"]) != f["sha256"]:
            (changed if f["name"] in UPLOADABLE else usb_only).append(f)
    return changed, usb_only


def github_check():
    sha, manifest = _stable_release()
    changed, usb_only = _compare(manifest)
    return {"ok": True, "version": manifest.get("version", "?"), "commit": sha[:7],
            "changed": [f["name"] for f in changed],
            "usb_only": [f["name"] for f in usb_only]}


def _download(sha, f):
    """Download one release file to <name>.dl and check its size and hash."""
    tmp = f["name"] + ".dl"
    r = _http_get("https://raw.githubusercontent.com/%s/%s/%s" % (GITHUB_REPO, sha, f["name"]))
    h, got = hashlib.sha256(), 0
    try:
        with open(tmp, "wb") as out:
            while True:
                b = r.raw.read(1024)
                if not b:
                    break
                out.write(b)
                h.update(b)
                got += len(b)
    finally:
        r.close()
    if got != f["size"] or binascii.hexlify(h.digest()).decode() != f["sha256"]:
        _remove(tmp)
        raise OSError("%s didn't match release.json (got %d bytes)" % (f["name"], got))
    return tmp


def github_install():
    sha, manifest = _stable_release()
    changed, usb_only = _compare(manifest)
    if not changed:
        return {"ok": True, "installed": [], "restart": False, "version": manifest.get("version", "?"),
                "usb_only": [f["name"] for f in usb_only], "message": "Already up to date"}
    if sum(f["size"] for f in changed) + 32 * 1024 > _free_bytes():
        raise OSError("not enough space on the Pico")
    done = []
    try:
        for f in changed:            # download and check everything first...
            done.append((_download(sha, f), f["name"]))
        for tmp, name in done:
            err = _syntax_error(tmp, name)
            if err:
                raise OSError(err)
    except Exception:
        for tmp, _ in done:
            _remove(tmp)
        raise
    for tmp, name in done:           # ...then swap them all in
        _swap_in(tmp, name)
    names = [n for _, n in done]
    return {"ok": True, "installed": names, "restart": "app.py" in names,
            "version": manifest.get("version", "?"), "usb_only": [f["name"] for f in usb_only],
            "message": "Installed %d file%s" % (len(names), "" if len(names) == 1 else "s")}


async def _restart_soon():
    await asyncio.sleep(1)
    machine.reset()


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
        query = parts[1].split("?")[1] if "?" in parts[1] else ""
        print("request:", peer, method, path)
        length = 0
        while True:
            h = await asyncio.wait_for(reader.readline(), 5)
            if not h or h == b"\r\n":
                break
            if h.lower().startswith(b"content-length:"):
                length = int(h.split(b":")[1])

        if path == "/api/upload" and method == "POST":
            name = query[5:] if query.startswith("name=") else ""
            status, msg = await _receive_upload(reader, name, length)
            _send_json(writer, {"ok": status == "200 OK", "message": msg}, status)
            await writer.drain()
            return
        if path == "/api/update" and method == "GET":
            info = {"free_kb": _free_bytes() // 1024, "files": UPLOADABLE,
                    "pending": _exists(PENDING_FILE), "last_error": None}
            try:
                with open("app_error.txt") as f:
                    info["last_error"] = f.read()[-1500:]
            except OSError:
                pass
            _send_json(writer, info)
            await writer.drain()
            return
        if path in ("/api/github", "/api/github/install"):
            # These block the Pico for a few seconds while it talks to GitHub;
            # the lights stay as they are.
            result = {}
            try:
                if path == "/api/github" and method == "GET":
                    result = github_check()
                elif method == "POST":
                    result = github_install()
                else:
                    raise OSError("use GET to check or POST to install")
                _send_json(writer, result)
            except Exception as e:
                print("github error:", e)
                _send_json(writer, {"ok": False, "message": str(e) or repr(e)}, "502 Bad Gateway")
            await writer.drain()
            if path.endswith("install") and result.get("restart"):
                asyncio.create_task(_restart_soon())
            return
        if path == "/api/restart" and method == "POST":
            _send_json(writer, {"ok": True, "message": "restarting"})
            await writer.drain()
            asyncio.create_task(_restart_soon())
            return

        body = {}
        if length:
            body = json.loads(await reader.readexactly(min(length, 2048)))

        if path == "/favicon.ico":
            path = "/icon-192.png"
        if method == "GET" and path in STATIC_FILES:
            name, ctype = STATIC_FILES[path]
            await _send_file(writer, name, ctype)
        elif path == "/api/state":
            if method == "POST" and "on" in body:
                set_on(bool(body["on"]))
            if method == "POST" and "brightness" in body:
                set_brightness(body["brightness"])
            _send_json(writer, public_state())
        elif path == "/api/lock" and method == "POST":
            if "locked" in body:
                set_locked(bool(body["locked"]))
            _send_json(writer, public_state())
        elif path == "/api/colours" and method == "POST":
            err = set_colours(None if body.get("reset") else body.get("colours"))
            if err:
                _send_json(writer, {"error": err}, "400 Bad Request")
            else:
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
    # Still running 30s after the web server started: confirm the update,
    # so the loader won't roll it back.
    await asyncio.sleep(30)
    if _exists(PENDING_FILE):
        _remove(PENDING_FILE)
        print("update confirmed")
    while True:
        await asyncio.sleep(3600)


asyncio.run(main())
