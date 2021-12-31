from utility.pokemon_classes import PokemonStats
import scrapers.pokemondb as pokemondb

class _Pokemon:
    def __init__(self, pokemon_name):
        self.name = pokemon_name
        self.evs = PokemonStats()
        self.ivs = PokemonStats()
        self.base_stats = pokemondb.get_base_stats(pokemon_name)

class _PokemonTrackingBase:
    def __init__(self):
        pass

    def 