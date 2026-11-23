# Loader for treeLights. Runs app.py; this file isn't updated over WiFi.
#
# If app.py fails to start straight after a WiFi update (app.py writes the
# file "update_pending" while it's on trial), the previous version, app.bak,
# is put back and the Pico restarts. Any startup error is saved to
# app_error.txt, which the update page shows.

import os
import sys
import time

import machine


def _exists(name):
    try:
        os.stat(name)
        return True
    except OSError:
        return False


try:
    import app  # runs until power off
except Exception as e:  # Ctrl-C (KeyboardInterrupt) still reaches the REPL
    sys.print_exception(e)
    try:
        with open("app_error.txt", "w") as f:
            sys.print_exception(e, f)
    except OSError:
        pass
    if _exists("update_pending") and _exists("app.bak"):
        print("New app.py failed; rolling back to the previous version")
        if _exists("app.bad"):
            os.remove("app.bad")
        os.rename("app.py", "app.bad")
        os.rename("app.bak", "app.py")
        os.remove("update_pending")
        time.sleep(1)
    else:
        # Nothing to roll back to. Wait so USB tools can get in, then retry.
        time.sleep(30)
    machine.reset()
