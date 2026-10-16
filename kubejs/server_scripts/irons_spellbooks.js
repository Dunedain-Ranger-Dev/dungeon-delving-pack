// Iron's Spells 'n Spellbooks: tie ink tiers and spell book tiers to the dungeon ores (DD-41).
// Each replaced recipe keeps its original shape; only the gating ingredient changes. Numbers are a first pass,
// to be tuned in playtesting.

ServerEvents.recipes(event => {
  const ingot = global.dungeonIngot

  // Replaces a recipe with an edited copy, keeping its original ID so nothing else (advancements, guides) breaks.
  const replace = (id, json) => {
    event.remove({ id: id })
    event.custom(json).id(id)
  }

  // Ink tiers, brewed in the alchemist cauldron. Ink rarity decides how strong a scroll can be inscribed.
  const inks = [
    ['uncommon', 'common', ingot.tier1],
    ['rare', 'uncommon', ingot.tier2],
    ['epic', 'rare', ingot.tier3],
    ['legendary', 'epic', ingot.tier4],
  ]
  inks.forEach(([ink, baseInk, gate]) => {
    replace(`irons_spellbooks:alchemist_cauldron/brew_${ink}_ink`, {
      type: 'irons_spellbooks:alchemist_cauldron_brew',
      base_fluid: { amount: 1000, id: `irons_spellbooks:${baseInk}_ink` },
      input: { item: gate },
      results: [{ amount: 250, id: `irons_spellbooks:${ink}_ink` }],
    })
  })

  // Spell books: each tier past copper needs that dungeon tier's ingot.
  replace('irons_spellbooks:iron_spell_book', {
    type: 'minecraft:crafting_shaped',
    pattern: ['CLL', 'CPP', 'CLL'],
    key: { C: { item: ingot.tier1 }, L: { tag: 'c:leathers' }, P: { item: 'minecraft:paper' } },
    result: { id: 'irons_spellbooks:iron_spell_book', count: 1 },
  })
  replace('irons_spellbooks:gold_spell_book', {
    type: 'minecraft:crafting_shaped',
    pattern: ['GMM', 'GHH', 'GMM'],
    key: { G: { item: ingot.tier2 }, M: { item: 'irons_spellbooks:arcane_essence' }, H: { item: 'irons_spellbooks:hogskin' } },
    result: { id: 'irons_spellbooks:gold_spell_book', count: 1 },
  })
  replace('irons_spellbooks:diamond_spell_book', {
    type: 'minecraft:crafting_shaped',
    pattern: ['DHH', 'TET', 'DHH'],
    key: {
      D: { item: ingot.tier3 },
      E: { item: 'minecraft:enchanted_book' },
      T: { item: 'irons_spellbooks:magic_cloth' },
      H: { item: 'irons_spellbooks:hogskin' },
    },
    result: { id: 'irons_spellbooks:diamond_spell_book', count: 1 },
  })
  replace('irons_spellbooks:netherite_spell_book', {
    type: 'minecraft:crafting_shaped',
    pattern: ['TNT', 'BRB', 'TLT'],
    key: {
      N: { item: ingot.tier4 },
      R: { item: 'irons_spellbooks:ruined_book' },
      T: { item: 'irons_spellbooks:magic_cloth' },
      B: { item: 'irons_spellbooks:blood_vial' },
      L: { item: 'irons_spellbooks:lightning_bottle' },
    },
    result: { id: 'irons_spellbooks:netherite_spell_book', count: 1 },
  })

  // Arcane ingot (used for upgrade orbs and more): its base metal becomes the common dungeon ingot.
  replace('irons_spellbooks:arcane_ingot', {
    type: 'minecraft:crafting_shaped',
    pattern: ['DDD', 'DWD', 'DDD'],
    key: { D: { item: 'irons_spellbooks:arcane_essence' }, W: { item: ingot.common } },
    result: { id: 'irons_spellbooks:arcane_ingot', count: 1 },
  })
})
