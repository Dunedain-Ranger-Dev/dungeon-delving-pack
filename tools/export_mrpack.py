"""Builds the installable modpack: dist/DungeonDelving-<version>.mrpack (the Modrinth pack format).

Run from the pack repository root: python tools/export_mrpack.py

- Every mod in pack.json's "modrinth" list is downloaded by the launcher straight from Modrinth (by pinned version
  id); the pack only lists it, with its hashes, so no one else's jar is redistributed.
- The Dungeon Delving jar (pack.json "mod_jar", built in the mod repository with ./gradlew build) and the pack's
  kubejs/ and config/ folders go in as overrides.

Testers import the .mrpack in Prism Launcher (Add Instance > Import) or the Modrinth App. The CurseForge app can't
read this format.
"""
import hashlib
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.modrinth.com/v2"
OVERRIDE_FOLDERS = ["kubejs", "config"]
SKIP_NAMES = {"README.md", ".gitkeep"}


def get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Ranger3462/dungeon-delving-pack (export_mrpack.py)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def pack_file(slug, version_id, minecraft):
    """The modrinth.index.json entry for one pinned Modrinth version, checked against the pack's Minecraft version."""
    version = get_json(f"{API}/version/{version_id}")
    if minecraft not in version["game_versions"] or "neoforge" not in version["loaders"]:
        sys.exit(f"{slug} version {version_id} ({version['version_number']}) isn't a NeoForge {minecraft} build")
    file = next((f for f in version["files"] if f["primary"]), version["files"][0])
    return {
        "path": f"mods/{file['filename']}",
        "hashes": {"sha1": file["hashes"]["sha1"], "sha512": file["hashes"]["sha512"]},
        "env": {"client": "required", "server": "required"},
        "downloads": [file["url"]],
        "fileSize": file["size"],
    }, f"{slug} {version['version_number']}"


def main():
    pack = json.loads((ROOT / "pack.json").read_text(encoding="utf-8"))
    mod_jar = (ROOT / pack["mod_jar"]).resolve()
    if not mod_jar.is_file():
        sys.exit(f"Dungeon Delving jar not found at {mod_jar}; run ./gradlew build in the mod repository first")

    files = []
    for slug, version_id in pack["modrinth"].items():
        entry, label = pack_file(slug, version_id, pack["minecraft"])
        files.append(entry)
        print("  " + label)

    index = {
        "formatVersion": 1,
        "game": "minecraft",
        "versionId": pack["version"],
        "name": pack["name"],
        "summary": pack["summary"],
        "files": files,
        "dependencies": {"minecraft": pack["minecraft"], "neoforge": pack["neoforge"]},
    }

    out = ROOT / "dist" / f"{pack['name'].replace(' ', '')}-{pack['version']}.mrpack"
    out.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("modrinth.index.json", json.dumps(index, indent=2))
        archive.write(mod_jar, f"overrides/mods/{mod_jar.name}")
        for folder in OVERRIDE_FOLDERS:
            for path in sorted((ROOT / folder).rglob("*")):
                if path.is_file() and path.name not in SKIP_NAMES:
                    archive.write(path, "overrides/" + path.relative_to(ROOT).as_posix())
    digest = hashlib.sha1(out.read_bytes()).hexdigest()
    print(f"Wrote {out.relative_to(ROOT)} ({len(files)} Modrinth mods + {mod_jar.name}), sha1 {digest}")


if __name__ == "__main__":
    main()
