// Ars Nouveau: tie spell book upgrades, armor upgrades and threads to the dungeon ores (DD-41).
// Each replaced recipe keeps its original ingredients except the gating ones. Numbers are a first pass,
// to be tuned in playtesting.

ServerEvents.recipes(event => {
  const ingot = global.dungeonIngot

  // Replaces a recipe with an edited copy, keeping its original ID so nothing else (advancements, guides) breaks.
  const replace = (id, json) => {
    event.remove({ id: id })
    event.custom(json).id(id)
  }

  // Apprentice spell book (tier 2): two quartz blocks become two tier 2 ingots.
  replace('ars_nouveau:apprentice_book_upgrade', {
    type: 'ars_nouveau:book_upgrade',
    category: 'misc',
    ingredients: [
      { item: 'ars_nouveau:novice_spell_book' },
      { tag: 'c:obsidians' },
      { tag: 'c:gems/diamond' },
      { tag: 'c:gems/diamond' },
      { tag: 'c:gems/diamond' },
      { item: ingot.tier2 },
      { item: ingot.tier2 },
      { tag: 'c:rods/blaze' },
      { tag: 'c:rods/blaze' },
    ],
    result: { count: 1, id: 'ars_nouveau:apprentice_spell_book' },
  })

  // Archmage spell book (tier 4): two emeralds become two tier 4 ingots.
  replace('ars_nouveau:archmage_book_upgrade', {
    type: 'ars_nouveau:book_upgrade',
    category: 'misc',
    ingredients: [
      { item: 'ars_nouveau:apprentice_spell_book' },
      { tag: 'c:ender_pearls' },
      { tag: 'c:ender_pearls' },
      { tag: 'c:ender_pearls' },
      { item: ingot.tier4 },
      { item: ingot.tier4 },
      { item: 'minecraft:totem_of_undying' },
      { item: 'minecraft:nether_star' },
      { item: 'ars_nouveau:wilden_tribute' },
    ],
    result: { count: 1, id: 'ars_nouveau:archmage_spell_book' },
  })

  // Mage armor upgrades: the first needs tier 1 ingots instead of blaze rods; the second needs a tier 3 ingot
  // instead of chorus fruit.
  replace('ars_nouveau:first_armor_upgrade', {
    type: 'ars_nouveau:armor_upgrade',
    pedestalItems: [{ item: ingot.tier1 }, { item: ingot.tier1 }],
    sourceCost: 2500,
    tier: 1,
  })
  replace('ars_nouveau:second_armor_upgrade', {
    type: 'ars_nouveau:armor_upgrade',
    pedestalItems: [{ tag: 'c:ender_pearls' }, { tag: 'c:ender_pearls' }, { item: ingot.tier3 }],
    sourceCost: 5000,
    tier: 2,
  })

  // Blank thread (base for all armor threads): gold nuggets become common dungeon ingots.
  replace('ars_nouveau:blank_thread', {
    type: 'minecraft:crafting_shaped',
    category: 'misc',
    key: { x: { item: 'ars_nouveau:magebloom_fiber' }, y: { item: ingot.common } },
    pattern: ['xxx', 'yyy', 'xxx'],
    result: { count: 1, id: 'ars_nouveau:blank_thread' },
  })
})
