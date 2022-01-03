from utility.pokemon import PokemonStats
from data.pokemon_list import all_pokemon
from data.egg_group_list import all_egg_groups
from difflib import get_close_matches
import pokebase

import scrapers

class PokemonDBScraperException(scrapers.ScraperException):
    """ Base exception class for this module. """
    pass

class WebRequestException(PokemonDBScraperException, scrapers.RequestException):
    """ A web request error occurred. Inherits from ThesaurusScraperException. """
    pass

class WebParseException(PokemonDBScraperException, scrapers.ParseException):
    """ An error occurred during webpage parsing. Inherits from ThesaurusScraperException. """
    pass

class WebSuggestionException(PokemonDBScraperException, scrapers.SuggestionException):
    """ 404 Received with a list of suggestions for spelling changes etc. Inherits from PokemonDBScraperException and scrapers.SuggestionException. """
    def __init__(self, *args):
        scrapers.SuggestionException.__init__(self, *args)

class Ability:
    def __init__(self, name: str, description: str, hidden: bool):
        self.name = name
        self.description = description
        self.hidden = hidden

    def __str__(self) -> str:
        return '{}{}: {}'.format(
            self.name,
            ' (Hidden Ability)' if self.hidden else '',
            self.description
        )

def _pokebase_lookup(key: str, lookup_fn, suggestion_list: list[str]):
    info = lookup_fn(key)
    if not hasattr(info, 'id'):
        matches = get_close_matches(key, suggestion_list)
        if len(matches) > 0:
            raise WebSuggestionException(matches)
        return None
    return info

def _get_pokemon_lookup(pokemon: str, lookup_fn):
    pokemon_info = _pokebase_lookup(pokemon.lower(), lookup_fn, all_pokemon)
    if pokemon_info is None:
        raise WebRequestException(f'Failed to find pokemon {pokemon}.')
    return pokemon_info

def _get_egg_group_lookup(egg_group: str, lookup_fn):
    egg_group_info = _pokebase_lookup(egg_group.lower(), lookup_fn, all_egg_groups)
    if egg_group_info is None:
        raise WebRequestException(f'Failed to find egg group {egg_group}.')
    return egg_group_info

def get_ev_yield_as_stats(pokemon: str) -> PokemonStats:
    """
    Looks up the EV yield of a pokemon using PokeBase library. 
    Either returns EV yield, or suggestions for pokemon names that are similar if that pokemon wasn't found.

        Parameters:
            pokemon (str): A pokemon to lookup in the db
        
        Returns:
            ev_yield (PokemonStats): The stats object with the EV Yield

        Exceptions:
            Throws:
                - WebRequestException
                - WebSuggestionException
    """
    pokemon_info = _get_pokemon_lookup(pokemon, pokebase.pokemon)
    return PokemonStats(*(int(pokemon_info.stats[i].effort) for i in range(6)))

def get_ev_yield(pokemon: str) -> list[str]:
    """
    Looks up the EV yield of a pokemon using https://pokemondb.net/pokedex/. 
    Either returns EV yield, or suggestions for pokemon names that are similar if that pokemon wasn't found.

        Parameters:
            pokemon (str): A pokemon to lookup in the db
        
        Returns:
            ev_yield (str): The EV yield of the pokemon

        Exceptions:
            Throws:
                - WebRequestException
                - WebParseException
                - WebSuggestionException
    """
    evs = get_ev_yield_as_stats(pokemon).to_pretty_dict()
    return [f'{val} {key}' for key, val in evs.items() if val != 0]

def get_types(pokemon: str) -> list[str]:
    """
    Looks up the type(s) of a pokemon using https://pokemondb.net/pokedex/. 
    Either returns type(s), or suggestions for pokemon names that are similar if that pokemon wasn't found.

        Parameters:
            pokemon (str): A pokemon to lookup in the db
        
        Returns:
            (success, return_data):
                - success of True indicates that the pokemon was found, and the return_data is a list of types
                - success of False indicates that the pokemon wasn't found, and the return_data is a list of suggested pokemon names that are similar

        Exceptions:
            Throws:
                - WebRequestException
                - WebParseException
    """
    pokemon_info = _get_pokemon_lookup(pokemon, pokebase.pokemon)
    return [poke_type.type.name.capitalize() for poke_type in pokemon_info.types]

def get_egg_groups(pokemon: str) -> list[str]:
    """
    Looks up the egg group(s) of a pokemon using https://pokemondb.net/pokedex/. 
    Either returns egg group(s), or suggestions for pokemon names that are similar if that pokemon wasn't found.

        Parameters:
            pokemon (str): A pokemon to lookup in the db
        
        Returns:
            (success, return_data):
                - success of True indicates that the pokemon was found, and the return_data is a list of egg groups
                - success of False indicates that the pokemon wasn't found, and the return_data is a list of suggested pokemon names that are similar

        Exceptions:
            Throws:
                - WebRequestException
                - WebParseException
    """
    pokemon_species = _get_pokemon_lookup(pokemon, pokebase.pokemon_species)
    return [egg_group.name.capitalize() for egg_group in pokemon_species.egg_groups]

def get_abilities(pokemon: str) -> list[Ability]:
    """
    Looks up the abilities of a pokemon using https://pokemondb.net/pokedex/. 
    Either returns abilities, or suggestions for pokemon names that are similar if that pokemon wasn't found.

        Parameters:
            pokemon (str): A pokemon to lookup in the db
        
        Returns:
            (success, return_data):
                - success of True indicates that the pokemon was found, and the return_data is a list of abilities
                - success of False indicates that the pokemon wasn't found, and the return_data is a list of suggested pokemon names that are similar

        Exceptions:
            Throws:
                - WebRequestException
                - WebParseException
    """
    pokemon_info = _get_pokemon_lookup(pokemon, pokebase.pokemon)
    abilities = []
    for ability in pokemon_info.abilities:
        poke_ability = pokebase.ability(ability.ability.name)
        description = ""
        for entry in poke_ability.effect_entries:
            if entry.language.name == "en":
                description = entry.short_effect
                break
        abilities.append(Ability(ability.ability.name.capitalize(), description, ability.is_hidden))
    return abilities

def get_evolutions(pokemon: str) -> list[Ability]:
    """
    Looks up all the evolutions of a pokemon using https://pokemondb.net/pokedex/.
    Either returns evolutions, or suggestions for pokemon names that are similar if that pokemon wasn't found.

        Parameters:
            pokemon (str): A pokemon to lookup in the db

        Returns:
            (success, return_data):
                - success of True indicates that the pokemon was found, and the return_data is a list of evolutions
                - success of False indicates that the pokemon wasn't found, and the return_data is a list of suggested pokemon names that are similar

        Exceptions:
            Throws:
                - WebRequestException
                - WebParseException
    """
    pokemon_species = _get_pokemon_lookup(pokemon, pokebase.pokemon_species)
    evolution_chain = pokebase.evolution_chain(pokemon_species.evolution_chain.id)

    def get_evolution_names(evolves_to_obj, evolution_names: list[str]):
        evolution_names.append(evolves_to_obj.species.name.capitalize())
        for obj in evolves_to_obj.evolves_to:
            get_evolution_names(obj, evolution_names)

    names = []
    get_evolution_names(evolution_chain.chain, names)
    return names

def get_egg_group_pokemon(egg_group: str) -> list[str]:
    """
    Looks up the pokemon in specified egg group using https://pokemondb.net/pokedex/. 
    Either returns list of pokemon, or suggestions for egg groups that are similar if none are found.

        Parameters:
            pokemon (str): A pokemon to lookup in the db

        Returns:
            (success, return_data):
                - success of True indicates that the egg group was found, and the return_data is a list of pokemon from that group
                - success of False indicates that the egg group wasn't found, and the return_data is a list of suggested egg group names that are similar

        Exceptions:
            Throws:
                - WebRequestException
                - WebParseException
    """
    egg_group_info = _get_egg_group_lookup(egg_group, pokebase.egg_group)
    return [pokemon.name.capitalize() for pokemon in egg_group_info.pokemon_species]

def get_base_stats(pokemon: str) -> PokemonStats:
    """
    Looks up the base stats of a pokemon using https://pokemondb.net/pokedex/.
    Either returns the base stats, or suggestions for pokemon names that are similar if that pokemon wasn't found.

        Parameters:
            pokemon (str): A pokemon to lookup in the db

        Returns:
            (success, return_data):
                - success of True indicates that the pokemon was found, and the return_data is the PokemonStats
                - success of False indicates that the pokemon wasn't found, and the return_data is a list of suggested pokemon names that are similar

        Exceptions:
            Throws:
                - WebRequestException
                - WebParseException
    """
    pokemon_info = _get_pokemon_lookup(pokemon, pokebase.pokemon)
    return PokemonStats(*(pokemon_info.stats[i].base_stat for i in range(6)))

def get_pokemon_image_url(pokemon: str) -> str:
    pass
