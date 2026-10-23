// Witcher (More RPG Classes): its steel ingot came straight from blasting an iron ingot, which took iron ingots away
// from Dungeon Delving's forging (a blast furnace should heat them). Steel now takes a Coke-Infused Iron Ingot
// (iron and coal, crafted) instead; Dungeon Delving adds that recipe.

ServerEvents.recipes(event => {
  event.remove({ id: 'witcher_rpg:steel_ingot_from_blasting_iron_ingot' })
})
