"""Writes the pack data that ties the RPG Series' gear to Dungeon Delving's forging (DD-81, DD-89).

Run from the pack repository root: python tools/rpg_forging.py
It reads each RPG Series mod's recipes from the Gradle cache (the Dungeon Delving mod's dev setup), and writes edited
copies under kubejs/data/<mod>/recipe/, which override the originals by ID. Run it again after updating those mods.

The ladder (DD-89): every piece keeps its own recipe, and gets a forged version beside it, written as
<mod>:forged/<path>. A forged piece is stronger by its ★, in its material's band (iron ★1-3, diamond ★4-5, netherite ★6-7):
- Iron gear: its own shape in forged parts: iron becomes armor plates, chain becomes chain links, gold in armor becomes
  rivets; leather, wool and hardened leather become our leather panels, cloth panels and hardened leather.
- Diamond gear: a forged iron piece smithed with a diamond (no template), ★4 or ★5.
- Netherite gear: its own smithing upgrade, which now carries a forged diamond piece's ★ up to ★6 or ★7 (plain stays plain).
- Every other smithing upgrade (Armory crystals and the like) keeps its inputs and the ★.
- Gold gear is left alone (Jewelcrafting will forge it).
- Witcher: its metals still map to dungeon ingots (its own swords' upgrades and armor diagrams take them), and its
  storage recipes are off; its own gear recipes use the mapped metals.
Bows, staves, wands and jewelry are left alone for now.
"""
import glob
import json
import os
import re
import shutil
import zipfile
from pathlib import Path

CACHE = os.path.expanduser("~/.gradle/caches/modules-2/files-2.1/maven.modrinth")
MODS = ["archers", "archers-expansion", "berserker-rpg-class", "elemental-wizards-rpg", "paladins-and-priests",
        "rogues-and-warriors", "witcher-rpg-class", "wizards", "armory-rpg-series", "arsenal-rpg-series",
        "forcemaster-rpg-class"]
# Optional mods the pack doesn't have; their recipes never load, so they're left alone.
ABSENT = {"betterend", "betternether", "loot_n_explore"}
NAMESPACES = ["archers", "archers_expansion", "berserker_rpg", "elemental_wizards_rpg", "paladins", "rogues",
              "witcher_rpg", "wizards", "armory_rpgs", "arsenal", "forcemaster_rpg"]

DD = "dungeondelving:"
PLATE, RIVETS, CHAIN = DD + "armor_plate", DD + "rivets", DD + "chain_links"
COKE_IRON = DD + "coke_infused_iron_ingot"


def tiers():
    """The dungeon ingot for each tier, read from the pack's startup script so the two never disagree."""
    text = Path("kubejs/startup_scripts/dungeon_ores.js").read_text(encoding="utf-8")
    return {k: v for k, v in re.findall(r"(tier\d): '([^']+)'", text)}


TIER = tiers()
# Parts and materials in gear (armor and weapons).
GEAR = {
    "minecraft:iron_ingot": PLATE,
    "minecraft:chain": CHAIN,
    "minecraft:leather": DD + "leather_panel",
    "mrpg_lib:hardened_leather": DD + "hardened_leather",
    "#minecraft:wool": DD + "cloth_panel",
    "minecraft:white_wool": DD + "cloth_panel",
    "witcher_rpg:steel_ingot": PLATE,
    "#witcher_rpg:steel_ingots": PLATE,
    # Witcher armor's main metal is forged like iron; its silver trim is the tier 1 ingot.
    "witcher_rpg:silver_ingot": PLATE,
    "#witcher_rpg:silver_ingots": TIER["tier1"],
}
ARMOR_ONLY = {"minecraft:gold_ingot": RIVETS}
# Witcher metals anywhere else (medallions, spell books, its own alloys).
WITCHER_METALS = {
    "witcher_rpg:steel_ingot": COKE_IRON,
    "#witcher_rpg:steel_ingots": COKE_IRON,
    "witcher_rpg:silver_ingot": TIER["tier2"],
    "#witcher_rpg:silver_ingots": TIER["tier2"],
    "witcher_rpg:dark_iron_ingot": TIER["tier1"],
    "witcher_rpg:dark_steel_ingot": TIER["tier3"],
    "witcher_rpg:meteorite_ingot": TIER["tier3"],
    "witcher_rpg:meteorite_silver_ingot": TIER["tier3"],
    "witcher_rpg:dimeritium_ingot": TIER["tier4"],
    "mrpg_lib:hardened_leather": DD + "hardened_leather",
}
WITCHER_DIAGRAMS = {"enhanced": "tier1", "superior": "tier2", "mastercrafted": "tier3", "grandmaster": "tier4"}
# Witcher swords past steel: (upgraded from, tier of the ingot it takes).
WITCHER_SWORDS = {"dark_iron": ("steel", "tier1"), "silver": ("steel", "tier2"), "dark_steel": ("steel", "tier3"),
                  "meteorite": ("steel", "tier3"), "meteorite_silver": ("silver", "tier3")}
ARMOR_SLOT = re.compile(r"_(head|chest|legs|feet|helmet|chestplate|leggings|boots)$")
TIER_ITEM = re.compile(r"^(?P<ns>[a-z_]+):(?P<mat>iron|golden|diamond|netherite)_(?P<kind>[a-z_]+)$")
STORAGE = re.compile(r"_(block|nugget|ingot)(_from_.*)?$")


def key_of(ingredient):
    if isinstance(ingredient, dict):
        return ingredient.get("item") or ("#" + ingredient["tag"] if "tag" in ingredient else None)
    return None


def as_ingredient(item_id):
    return {"tag": item_id[1:]} if item_id.startswith("#") else {"item": item_id}


def remap(ingredient, table):
    if isinstance(ingredient, list):
        return [remap(i, table) for i in ingredient]
    key = key_of(ingredient)
    return as_ingredient(table[key]) if key in table else ingredient


def result_id(recipe):
    result = recipe.get("result", {})
    return result.get("id") or result.get("item")


def absent(recipe):
    return any(c.get("type") == "neoforge:mod_loaded" and c.get("modid") in ABSENT for c in recipe.get("neoforge:conditions", []))


def off(recipe):
    """The recipe, never loading."""
    return {**recipe, "neoforge:conditions": [{"type": "neoforge:false"}]}


def forged_upgrade(base, addition, result):
    """A smithing upgrade that only takes a forged (starred) base, and moves it up a band."""
    return {"type": DD + "forged_smithing", "template": [], "base": as_ingredient(base), "addition": as_ingredient(addition),
            "result": {"id": result, "count": 1}}


def upgrade(base, addition, result, template=None):
    return {"type": DD + "starred_smithing", "template": as_ingredient(template) if template else [],
            "base": as_ingredient(base), "addition": as_ingredient(addition), "result": {"id": result, "count": 1}}


# Parts that carry the forging or crafting ★ (DD-88: leather and cloth panels are starred now too).
STARRED_PARTS = (PLATE, RIVETS, CHAIN, DD + "leather_panel", DD + "cloth_panel", DD + "hardened_leather", DD + "straps")


def is_starred(keys):
    return any(key_of(v) in STARRED_PARTS for v in keys.values())


def load():
    recipes = {}
    for mod in MODS:
        for jar in glob.glob(os.path.join(CACHE, mod, "*", "*", "*.jar")):
            if jar.endswith("-sources.jar"):
                continue
            with zipfile.ZipFile(jar) as z:
                for name in z.namelist():
                    match = re.match(r"data/([a-z_]+)/recipe/(.+)\.json$", name)
                    if match and match.group(1) in NAMESPACES:
                        recipes[f"{match.group(1)}:{match.group(2)}"] = json.loads(z.read(name))
    return recipes


def rework(rid, recipe, all_ids):
    """What to write for one recipe: a list of (recipe id, recipe), and why. Writing a recipe's own id replaces it."""
    kind = recipe.get("type")
    out = result_id(recipe) or ""
    ns, path = rid.split(":", 1)
    forged_id = f"{ns}:forged/{path}"
    tier = TIER_ITEM.match(out)
    if absent(recipe):
        return [], "needs a mod the pack doesn't have"

    if ns == "witcher_rpg":
        sword = re.match(r"witcher_rpg:(.+)_witcher_sword$", out)
        if sword and sword.group(1) in WITCHER_SWORDS:
            source, t_ = WITCHER_SWORDS[sword.group(1)]
            return [(rid, upgrade(f"witcher_rpg:{source}_witcher_sword", TIER[t_], out))], f"upgrade of the {source} sword"
        diagram = key_of(recipe.get("template")) or ""
        if kind == "minecraft:smithing_transform" and diagram.startswith("witcher_rpg:") and diagram.endswith("_diagram"):
            t_ = WITCHER_DIAGRAMS[diagram.split(":")[1][:-len("_diagram")]]
            return [(rid, {**recipe, "type": DD + "starred_smithing", "addition": as_ingredient(TIER[t_])})], f"diagram upgrade, {t_} ingot"
        if kind == "minecraft:crafting_shaped" and STORAGE.search(out) and any(key_of(v) in WITCHER_METALS for v in recipe["key"].values()):
            return [(rid, off(recipe))], "Witcher metal storage, unused"
        if kind == "minecraft:crafting_shaped" and STORAGE.search(out) and out in WITCHER_METALS:
            return [(rid, off(recipe))], "Witcher metal, unused"

    if tier:
        mat, base = tier.group("mat"), f"{tier.group('ns')}:iron_{tier.group('kind')}"
        if mat == "golden":
            return [], "gold, left for Jewelcrafting"
        if mat == "diamond" and kind == "minecraft:crafting_shaped":
            if base in all_ids:
                return [(forged_id, forged_upgrade(base, "minecraft:diamond", out))], "forged: an iron piece and a diamond"
            return [], "diamond piece with no iron version"
        if mat == "netherite" and kind == "minecraft:smithing_transform":
            return [(rid, {**recipe, "type": DD + "starred_smithing"})], "netherite upgrade carries the stars"

    if kind == "minecraft:smithing_transform":
        return [(rid, {**recipe, "type": DD + "starred_smithing"})], "upgrade keeps the stars"

    if kind == "minecraft:crafting_shaped":
        armor = bool(ARMOR_SLOT.search(out))
        weapon = bool(tier) or out.startswith("witcher_rpg:") and out.endswith("_witcher_sword")
        writes = []
        if ns == "witcher_rpg":
            own = {k: remap(v, WITCHER_METALS) for k, v in recipe["key"].items()}
            if own != recipe["key"]:
                writes.append((rid, {**recipe, "key": own}))
        if armor or weapon:
            table = {**GEAR, **(ARMOR_ONLY if armor else {})}
            keys = {k: remap(v, table) for k, v in recipe["key"].items()}
            if is_starred(keys):
                return writes + [(forged_id, {**recipe, "key": keys, "type": DD + "starred_shaped"})], "forged version beside its own"
            return writes, "gear with no forged parts"
        if writes:
            return writes, "Witcher metals to dungeon ingots"
    return [], "not gear"


def main():
    recipes = load()
    ids = {result_id(r) for r in recipes.values()} | set(recipes)
    for ns in NAMESPACES:
        shutil.rmtree(Path("kubejs/data") / ns / "recipe", ignore_errors=True)
    counts = {}
    report = []
    for rid in sorted(recipes):
        recipe = recipes[rid]
        if recipe.get("type") not in ("minecraft:crafting_shaped", "minecraft:smithing_transform"):
            continue
        writes, why = rework(rid, recipe, ids)
        counts[why] = counts.get(why, 0) + 1
        report.append(f"{'*' if writes else ' '} {rid}: {why}")
        for wid, edited in writes:
            ns, path = wid.split(":", 1)
            target = Path("kubejs/data") / ns / "recipe" / (path + ".json")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(edited, indent=2) + "\n", encoding="utf-8", newline="\n")
    Path("tools/rpg_forging_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
    for why, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"{n:4} {why}")


if __name__ == "__main__":
    main()
