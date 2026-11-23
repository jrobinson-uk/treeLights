"""Write release.json: the list of Pico files, with sizes and SHA-256 hashes.

The Pico's "Check for updates" button reads release.json from the commit
tagged "stable", and only installs files that match it.

To release what's in this folder:

    python3 make_release.py 2026.11.23
    git add -A && git commit -m "Release 2026.11.23"
    git push
    git tag -f stable && git push -f origin stable

The version name is optional; it defaults to today's date.
"""

import datetime
import hashlib
import json
import os
import sys

FILES = ["main.py", "app.py", "index.html", "update.html", "manifest.json",
         "icon-192.png", "icon-512.png"]

here = os.path.dirname(os.path.abspath(__file__))
version = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime("%Y.%m.%d")
files = []
for name in FILES:
    data = open(os.path.join(here, name), "rb").read()
    files.append({"name": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})

with open(os.path.join(here, "release.json"), "w") as f:
    json.dump({"version": version, "files": files}, f, indent=1)
    f.write("\n")
print("release.json: version %s, %d files" % (version, len(files)))
