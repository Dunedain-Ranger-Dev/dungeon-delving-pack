"""Writes the pack data that keeps Apotheosis to dungeons (DD-30, DD-31).

Run from the pack repository root: python tools/apotheosis_dungeon_only.py [path/to/apotheosis.jar]
With no path, it looks for Apotheosis 8.9.0 in the Gradle cache (the Dungeon Delving mod's dev setup). The jar is only
read, to copy Apotheosis's own files with our changes; output goes to kubejs/data/apotheosis/, which overrides them.

- Loot modifiers: affix gear injection and conversion, and gem drops from chests and mobs, only apply in the dungeon
  dimension (a location_check condition on each).
- Natural invader spawns are off in every dimension (the invader spawn rules data map is replaced with nothing). The
  Dungeon Delving mod calls invaders into dungeons from their spawners instead.
- Every invader and elite may only appear in the dungeon dimension.
- The random affix items augment (monsters wearing affix gear) also applies to spawner mobs, so dungeon mobs can wear
  it; the mod strips it from anything outside a dungeon.

The mod also keeps world tiers in step with dungeon tiers (Haven outside), and strips affix gear and gems from drops
outside dungeons, as a catch-all.
"""
import glob
import json
import os
import sys
import zipfile
from pathlib import Path

OUT = Path("kubejs/data/apotheosis")
DUNGEON = "dungeondelving:dungeon"
IN_DUNGEON = {"condition": "minecraft:location_check", "predicate": {"dimension": DUNGEON}}
LOOT_MODIFIERS = ["affix_conversion", "affix_loot_injection", "gem_loot_injection", "gem_entity_drops",
                  "gem_entity_drops_from_real_players"]


def find_jar():
    if len(sys.argv) > 1:
        return sys.argv[1]
    # The mod repository's dev runs fetch it from CurseForge (CurseMaven): curse.maven:apotheosis-<project>:<file>.
    cache = os.path.expanduser("~/.gradle/caches/modules-2/files-2.1/curse.maven/apotheosis-313970/8993983")
    found = glob.glob(os.path.join(cache, "*", "apotheosis-313970-8993983.jar"))
    if not found:
        sys.exit("Apotheosis jar not found; pass its path")
    return found[0]


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8", newline="\n")


def main():
    jar = zipfile.ZipFile(find_jar())

    def read(name):
        return json.loads(jar.read(f"data/apotheosis/{name}"))

    for name in LOOT_MODIFIERS:
        modifier = read(f"loot_modifiers/{name}.json")
        modifier["conditions"] = [IN_DUNGEON] + [c for c in modifier.get("conditions", []) if c != IN_DUNGEON]
        write(OUT / "loot_modifiers" / f"{name}.json", modifier)

    write(OUT / "data_maps/dimension_type/invader_spawn_rules.json", {"replace": True, "values": {}})

    for path in jar.namelist():
        if path.endswith(".json") and (path.startswith("data/apotheosis/apothic_invaders/") or path.startswith("data/apotheosis/apothic_elites/")):
            mob = json.loads(jar.read(path))
            mob.setdefault("basic_data", {}).setdefault("constraints", {})["dimensions"] = [DUNGEON]
            write(OUT / path[len("data/apotheosis/"):], mob)

    augment = read("apothic_augments/random_affix_items.json")
    augment["conditions"] = [{"type": "apotheosis:is_monster"}]
    write(OUT / "apothic_augments/random_affix_items.json", augment)
    print("apotheosis dungeon-only data written")


if __name__ == "__main__":
    main()
