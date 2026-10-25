"""CurseForge API helpers for the pack's tools.

By default the calls go through api.curse.tools, a community mirror of CurseForge's API that needs no key (only mod
files' fingerprints and ids are sent). Set CURSEFORGE_OFFICIAL=1 to use CurseForge's own API instead, with the key in
CURSEFORGE_API_KEY (or, on Windows, the user's saved environment). The key is never printed.
"""
import json
import os
import sys
import urllib.request

OFFICIAL = os.environ.get("CURSEFORGE_OFFICIAL") == "1"
API = "https://api.curseforge.com/v1" if OFFICIAL else "https://api.curse.tools/v1"
MINECRAFT = 432


def api_key():
    key = os.environ.get("CURSEFORGE_API_KEY")
    if not key and sys.platform == "win32":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as env:
                key = winreg.QueryValueEx(env, "CURSEFORGE_API_KEY")[0]
        except OSError:
            key = None
    if not key:
        sys.exit("Set CURSEFORGE_API_KEY (a key from console.curseforge.com) first")
    return key


def call(path, body=None):
    """A CurseForge API call: GET, or POST with a JSON body."""
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "Ranger3462/dungeon-delving-pack"}
    if OFFICIAL:
        headers["x-api-key"] = api_key()
    request = urllib.request.Request(API + path, data=data, method="POST" if data else "GET", headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def fingerprint(data):
    """CurseForge's file fingerprint: MurmurHash2 (seed 1) of the file with whitespace bytes (tab, LF, CR, space) removed."""
    data = bytes(b for b in data if b not in (9, 10, 13, 32))
    m, r = 0x5BD1E995, 24
    length = len(data)
    h = (1 ^ length) & 0xFFFFFFFF
    i = 0
    while length - i >= 4:
        k = data[i] | data[i + 1] << 8 | data[i + 2] << 16 | data[i + 3] << 24
        k = (k * m) & 0xFFFFFFFF
        k ^= k >> r
        k = (k * m) & 0xFFFFFFFF
        h = (h * m) & 0xFFFFFFFF
        h ^= k
        i += 4
    rest = length - i
    if rest == 3:
        h ^= data[i + 2] << 16
    if rest >= 2:
        h ^= data[i + 1] << 8
    if rest >= 1:
        h ^= data[i]
        h = (h * m) & 0xFFFFFFFF
    h ^= h >> 13
    h = (h * m) & 0xFFFFFFFF
    h ^= h >> 15
    return h
