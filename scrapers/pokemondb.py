import requests
from bs4 import BeautifulSoup

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

def _parse_pokemon_suggestions(pokemon, soup):
    suggestions = []
    for li in soup.find_all('li'):
        a = li.find('a', href=True)
        if a is None:
            raise WebParseException('Failed to parse "a" from "li" for word suggestions.')

        if a['href'] is not None and len(a['href'].split('/')) == 3:
            suggestions.append(a['href'].split('/')[-1])

    if len(suggestions) == 0:
        raise WebParseException(f'Failed to find any suggestions for {pokemon}.')
    return suggestions

def get_ev_yield(pokemon: str):
    """
    Looks up the EV yield of a pokemon using https://pokemondb.net/pokedex/. 
    Either returns EV yield, or suggestions for pokemon names that are similar if that pokemon wasn't found.

        Parameters:
            pokemon (str): A word to lookup the synonym for
        
        Returns:
            (success, return_data):
                - success of True indicates that ev yield was found, and the return_data is the EV yield as a string
                - success of False indicates that the pokemon wasn't found, and the return_data is a list of suggested pokemon names that are similar

        Exceptions:
            Throws:
                - WebRequestException
                - WebParseException
    """
    url = f'https://pokemondb.net/pokedex/{pokemon}'
    response = requests.get(url)
    if response.status_code == 404 and response.text is not None:
        # 404 gives useful information, so we still want to parse it
        pass
    else:
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise WebRequestException(f'Failed to GET request to URL {url}. Error: {e}')

    # Make soup
    try:
        soup = BeautifulSoup(response.text, 'lxml')
    except Exception as e:
        raise WebParseException(f'Failed to parse response using lxml. Error: {e}')

    # Parse the EV yield/suggestion
    if response.status_code == 404:
        try:
            return (False, _parse_pokemon_suggestions(pokemon, soup))
        except WebParseException as e:
            raise WebParseException(f'No entry found for {pokemon}. Failed to parse the suggestions. Error: {e}')
    else:
        # Parse EV yield
        ev_yield_name = soup.find('th', text='EV yield')
        if ev_yield_name is None:
            raise WebParseException(f'Failed to find EV yield for {pokemon}. Failed to parse "th" with text "EV yield" from webpage.')

        # Parse the EV value
        ev_value = ev_yield_name.parent.find('td', {'class': 'text'})
        if ev_value is None:
            raise WebParseException(f'Failed to find EV yield for {pokemon}. Failed to parse "td" from "EV yield".')
        return (True, ev_value.get_text(strip=True))

def get_type(pokemon: str) -> list[str]:
    """
    Looks up the type(s) of a pokemon using https://pokemondb.net/pokedex/. 
    Either returns type(s), or suggestions for pokemon names that are similar if that pokemon wasn't found.

        Parameters:
            pokemon (str): A word to lookup the synonym for
        
        Returns:
            (success, return_data):
                - success of True indicates that ev yield was found, and the return_data is a list of EV's
                - success of False indicates that the pokemon wasn't found, and the return_data is a list of suggested pokemon names that are similar

        Exceptions:
            Throws:
                - WebRequestException
                - WebParseException
    """
    url = f'https://pokemondb.net/pokedex/{pokemon}'
    response = requests.get(url)
    if response.status_code == 404 and response.text is not None:
        # 404 gives useful information, so we still want to parse it
        pass
    else:
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise WebRequestException(f'Failed to GET request to URL {url}. Error: {e}')

    # Make soup
    try:
        soup = BeautifulSoup(response.text, 'lxml')
    except Exception as e:
        raise WebParseException(f'Failed to parse response using lxml. Error: {e}')

    # Parse the type/suggestion
    if response.status_code == 404:
        try:
            return (False, _parse_pokemon_suggestions(pokemon, soup))
        except WebParseException as e:
            raise WebParseException(f'No entry found for {pokemon}. Failed to parse the suggestions. Error: {e}')
    else:
        # Parse the Type
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
        return (True, types)
