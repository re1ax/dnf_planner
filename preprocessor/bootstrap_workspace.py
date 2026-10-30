#!/usr/bin/env python3
"""Extract a checksum-pinned official Ubuntu SWI core inside this delivery.

No system installation, sudo, registry or global environment changes. The
vendored .deb is preferred; --download can retrieve the identical package if
it is absent. On Windows, existing Ubuntu WSL and dpkg-deb are required.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request

HERE = Path(__file__).resolve().parent
RUNTIME = HERE.parent / "runtime" / "linux-x64"
PACKAGE = "swi-prolog-core_9.2.9+dfsg-1.1build1_amd64.deb"
URL = "https://archive.ubuntu.com/ubuntu/pool/universe/s/swi-prolog/" + PACKAGE
SHA256 = "f0bca591d13b2a651038ab5b2a8b979e7878ac2696bed080764809c9505c093d"


def linux_path(path):
    p = str(Path(path).resolve())
    return "/mnt/" + p[0].lower() + p[2:].replace("\\", "/") if os.name == "nt" else p


def bootstrap(download=False):
    RUNTIME.mkdir(parents=True, exist_ok=True)
    package = RUNTIME / PACKAGE
    if not package.is_file():
        if not download:
            raise FileNotFoundError("bundled SWI package missing; use --download")
        with urllib.request.urlopen(URL, timeout=60) as response:
            package.write_bytes(response.read())
    actual = hashlib.sha256(package.read_bytes()).hexdigest()
    if actual != SHA256:
        raise ValueError("SWI package SHA256 mismatch")
    root = RUNTIME / "root"
    root.mkdir(exist_ok=True)
    command = ["dpkg-deb", "-x", linux_path(package), linux_path(root)]
    if os.name == "nt":
        command = ["wsl.exe", "-e"] + command
    subprocess.run(command, check=True)
    return root


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    print(bootstrap(args.download))
