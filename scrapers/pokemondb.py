import requests
from bs4 import BeautifulSoup
from requests.api import request
from utility.pokemon_classes import PokemonStats

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

def _parse_suggestions(search_item, soup):
    suggestions = []
    for li in soup.find_all('li'):
        a = li.find('a', href=True)
        if a is None:
            raise WebParseException('Failed to parse "a" from "li" for word suggestions.')

        if a['href'] is not None and len(a['href'].split('/')) == 3:
            suggestions.append(a['href'].split('/')[-1].replace('-', ' '))

    if len(suggestions) == 0:
        raise WebParseException(f'Failed to find any suggestions for {search_item}.')
    return suggestions

def _get_page_info(search_item, url):
    response = requests.get(url)
    soup = None
    if response.text is not None:
        # Create soup
        try:
            soup = BeautifulSoup(response.text, 'lxml')
        except Exception as e:
            raise WebParseException(f'Failed to parse response using lxml. Error: {e}')

    # Check for errors
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        if response.status_code == 404 and soup is not None:
            raise WebSuggestionException(_parse_suggestions(search_item, soup))
        else:
            raise WebRequestException(f'Failed to GET request to URL {url}. Error: {e}')

    if soup is None:
        raise WebParseException(f'Failed to parse soup for URL {url}.')
    return soup

def _get_pokemon_pokedex_entry(pokemon):
    return _get_page_info(pokemon, f'https://pokemondb.net/pokedex/{pokemon}')

def _get_egg_group(egg_group):
    return _get_page_info(egg_group, f'https://pokemondb.net/egg-group/{egg_group}')

def get_ev_yield(pokemon: str) -> str:
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
    # Parse EV yield
    soup = _get_pokemon_pokedex_entry(pokemon)
    ev_yield_name = soup.find('th', text='EV yield')
    if ev_yield_name is None:
        raise WebParseException(f'Failed to find EV yield for {pokemon}. Failed to parse "th" with text "EV yield" from webpage.')

    # Parse the EV value
    ev_value = ev_yield_name.parent.find('td', {'class': 'text'})
    if ev_value is None:
        raise WebParseException(f'Failed to find EV yield for {pokemon}. Failed to parse "td" from "EV yield".')
    return ev_value.get_text(strip=True).split(', ')

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
    # Parse the Type
    soup = _get_pokemon_pokedex_entry(pokemon)
    type_name = soup.find('th', text='Type')
    if type_name is None:
        raise WebParseException(f'Failed to find Type for {pokemon}. Failed to parse "th" with text "Type" from webpage.')
    
    # Parse the Type value
    type_value_group = type_name.parent.find('td')
    if type_value_group is None:
        raise WebParseException(f'Failed to find Type for {pokemon}. Failed to parse "td" from "Type".')

    # Read out all the types
    types = [span.get_text(strip=True) for span in type_value_group.find_all('a')]
    if len(types) == 0:
        raise WebParseException(f'Failed to find Type for {pokemon}. Failed to find any "a" in the "td" element for "Type".')
    return types

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
    # Parse the Type
    soup = _get_pokemon_pokedex_entry(pokemon)
    egg_groups_name = soup.find('th', text='Egg Groups')
    if egg_groups_name is None:
        raise WebParseException(f'Failed to find Egg Groups for {pokemon}. Failed to parse "th" with text "Egg Groups" from webpage.')
    
    # Parse the Type value
    egg_groups_list = egg_groups_name.parent.find('td')
    if egg_groups_list is None:
        raise WebParseException(f'Failed to find Type for {pokemon}. Failed to parse "td" from "Egg Groups".')

    # Read out all the types
    egg_groups = [span.get_text(strip=True) for span in egg_groups_list.find_all('a')]
    if len(egg_groups) == 0:
        raise WebParseException(f'Failed to find Type for {pokemon}. Failed to find any "a" in the "td" element for "Egg Groups".')
    return egg_groups

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
    # Parse the Type
    soup = _get_pokemon_pokedex_entry(pokemon)
    abilities_name = soup.find('th', text='Abilities')
    if abilities_name is None:
        raise WebParseException(f'Failed to find Abilities for {pokemon}. Failed to parse "th" with text "Abilities" from webpage.')
    
    # Parse the Type value
    abilities_list = abilities_name.parent.find('td')
    if abilities_list is None:
        raise WebParseException(f'Failed to find Type for {pokemon}. Failed to parse "td" from "Abilities".')

    abilities = []
    for a in abilities_list.find_all('a'):
        name = a.get_text(strip=True)
        description = ''
        if a.has_attr('title'):
            description = a['title']
        hidden = a.parent.name == 'small'
        abilities.append(Ability(name, description, hidden))
    if len(abilities) == 0:
        raise WebParseException(f'Failed to find Abilities for {pokemon}. Failed to find any "a" in the "td" element for "Abilities".')
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
    # Parse the Type
    soup = _get_pokemon_pokedex_entry(pokemon)
    evolutions = []
    for evolution_list in soup.find_all('div', {'class': 'infocard-list-evo'}):
        for a in evolution_list.find_all('a', {'class': 'ent-name'}):
            evolution = a.get_text(strip=True)
            if evolution not in evolutions:
                evolutions.append(evolution)
    if len(evolutions) == 0:
        raise WebParseException(f'Failed to find Evolutions for {pokemon}. Failed to find any "a" in the "div" element with class "infocard-list-evo".')
    return evolutions

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
    soup = _get_egg_group(egg_group)
    pokemon = []
    for span in soup.find_all('a', {'class': 'ent-name'}):
        pokemon.append(span.get_text(strip=True))
    if len(pokemon) == 0:
        raise WebParseException(f'Failed to find pokemon for egg group {egg_group}. Failed to find any "a" in the web page with class "ent-name".')
    return pokemon

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
    # Parse the Vitals Table
    soup = _get_pokemon_pokedex_entry(pokemon)
    base_stats = PokemonStats()
    base_stats_header = soup.find('h2', text='Base stats')
    if base_stats_header is None:
        raise WebParseException(f'Failed to find Base Stats for {pokemon}. Failed to parse "h2" with text "Base stats" from webpage.')
    vitals = base_stats_header.parent.find('table', {'class': 'vitals-table'})
    if vitals is None:
        raise WebParseException(f'Failed to find Base Stats for {pokemon}. Failed to parse "table" with class "vitals-table" from Base stats div.')

    rows = vitals.find_all('tr')
    if len(rows) == 0:
        raise WebParseException(f'Failed to find Base Stats for {pokemon}. Found 0 entries for "tr" from Vitals Table.')
    for row in vitals.find_all('tr'):
        stat = row.find('th')
        if stat is None:
            raise WebParseException(f'Failed to find Base Stats for {pokemon}. Failed to parse "th" from Vitals Table row.')
        stat_text = stat.get_text(strip=True).lower().replace('. ', '_')

        if not hasattr(base_stats, stat_text):
            raise WebParseException(f'Failed to find Base Stats for {pokemon}. PokemonStats object does not contain an attribute called {stat_text}.')

        base_stat = row.find('td')
        if base_stats is None:
            raise WebParseException(f'Failed to find Base Stats for {pokemon}. Failed to parse the "td" from Vitals Table row.')
        setattr(base_stats, stat_text, int(base_stat.get_text(strip=True)))
    return base_stats

def get_pokemon_image_url(pokemon: str) -> str:
    url = f'https://img.pokemondb.net/artwork/{pokemon}.jpg'
    response = requests.get(url)
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise WebRequestException(f'Failed to GET request to URL {url}. Error: {e}')
    return url
