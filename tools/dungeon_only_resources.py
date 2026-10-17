"""Writes the pack data that makes the magic mods' upgrade materials dungeon-only (DD-42).

Run from the pack repository root: python tools/dungeon_only_resources.py
Output goes to kubejs/data/, which loads as a data pack:

- dungeondelving:dungeon_only item tag: Iron's Spells upgrade materials. The Dungeon Delving mod removes these
  from all loot generated outside dungeons (structure chests, mob drops, block drops).
- Iron's Spells mithril ore no longer generates in the overworld; it shows up on dungeon resource markers from
  tier 2 instead (dungeondelving:dungeon_resources/tier_<n> block tags).
- Dungeon chests get extra magic loot by tier, through NeoForge's add_table loot modifier.

Consumables (scrolls, inks, elixirs) stay in overworld loot. Boss and mob signature drops (e.g. the Necronomicon)
are left alone.
"""
import json
from pathlib import Path

DATA = Path("kubejs/data")
IRONS = "irons_spellbooks"
PACK = "dungeondelving_pack"
TIERS = (1, 2, 3, 4)
INK = {1: "uncommon_ink", 2: "rare_ink", 3: "epic_ink", 4: "legendary_ink"}

# Permanent-upgrade materials: only found in dungeons.
DUNGEON_ONLY = [
    "arcane_essence",
    "blank_rune",
    "ruined_book",
    "magic_cloth",
    "cinder_essence",
    "mithril_scrap",
    "raw_mithril",
    "mithril_ore",
    "deepslate_mithril_ore",
    "rotten_spell_book",
]


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8", newline="\n")


def item(name, weight, low=1, high=1):
    entry = {"type": "minecraft:item", "name": f"{IRONS}:{name}", "weight": weight}
    if (low, high) != (1, 1):
        entry["functions"] = [{"function": "minecraft:set_count", "count": {"type": "minecraft:uniform", "min": low, "max": high}}]
    return entry


def nothing(weight):
    return {"type": "minecraft:empty", "weight": weight}


def room(t):
    """A small chance of a magic material in each loot-marker chest."""
    entries = [item("arcane_essence", 10, 1, 1 + t), item("blank_rune", 4, 1, t), item(INK[t], 3), nothing(24)]
    if t >= 2:
        entries.append(item("magic_cloth", 2))
    if t >= 3:
        entries += [item("cinder_essence", 2), item("ruined_book", 1)]
    return {"type": "minecraft:chest", "pools": [{"rolls": 1, "entries": entries}]}


def objective(t):
    """The objective chest's magic payout: always some arcane essence, plus two more rolls."""
    guaranteed = [item("arcane_essence", 1, 2, 2 + 2 * t)]
    extra = [item("blank_rune", 6, 1, t), item(INK[t], 4)]
    if t >= 2:
        extra += [item("magic_cloth", 4, 1, t), item("ruined_book", 2), item("mithril_scrap", 3, 1, t)]
    if t >= 3:
        extra.append(item("cinder_essence", 3, 1, t - 1))
    return {"type": "minecraft:chest", "pools": [{"rolls": 1, "entries": guaranteed}, {"rolls": 2, "entries": extra}]}


write(DATA / "dungeondelving/tags/item/dungeon_only.json", {"replace": False, "values": [f"{IRONS}:{i}" for i in DUNGEON_ONLY]})

# Turn off Iron's Spells' overworld mithril ore; dungeons from tier 2 have it instead.
write(DATA / f"{IRONS}/neoforge/biome_modifier/add_mithril_ore.json", {"type": "neoforge:none"})
for t in TIERS:
    write(DATA / f"dungeondelving/tags/block/dungeon_resources/tier_{t}.json",
          {"replace": False, "values": [f"{IRONS}:mithril_ore"] if t >= 2 else []})

modifiers = []
for t in TIERS:
    for kind, table in (("room", room(t)), ("objective", objective(t))):
        name = f"dungeon_magic/{kind}_tier_{t}"
        write(DATA / f"{PACK}/loot_table/{name}.json", table)
        write(DATA / f"{PACK}/loot_modifiers/{name}.json", {
            "type": "neoforge:add_table",
            "conditions": [{"condition": "neoforge:loot_table_id", "loot_table_id": f"dungeondelving:chests/tier_{t}/{kind}"}],
            "table": f"{PACK}:{name}",
        })
        modifiers.append(f"{PACK}:{name}")
write(DATA / "neoforge/loot_modifiers/global_loot_modifiers.json", {"replace": False, "entries": modifiers})
print(f"Wrote {len(DUNGEON_ONLY)} dungeon-only items and {len(modifiers)} dungeon loot modifiers")
