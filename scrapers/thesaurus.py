import requests
from bs4 import BeautifulSoup

from scrapers import ScraperException

class ThesaurusScraperException(ScraperException):
    """ Base exception class for this module. """
    pass

class WebRequestException(ThesaurusScraperException):
    """ A web request error occurred. Inherits from ThesaurusScraperException. """
    pass

class WebParseException(ThesaurusScraperException):
    """ An error occurred during webpage parsing. Inherits from ThesaurusScraperException. """
    pass

def get_synonym(word: str) -> tuple[bool, list[str]]:
    """
    Looks up the synonym to a word using https://www.thesaurus.com/browse. 
    Either returns synonyms, or suggestions for words that are similar if that word wasn't found.

        Parameters:
            word (str): A word to lookup the synonym for
        
        Returns:
            (success, result_list) (tuple[bool, list[str]]):
                - success of True indicates that synonyms were found, and the result_list is a list of synonyms
                - success of False indicates that the word didn't match anything in the thesaurus, and the result_list is a list of suggested words

        Exceptions:
            Throws:
                - WebRequestException
                - WebParseException
    """
    # Pull the webpage
    url = f'https://www.thesaurus.com/browse/{word}'
    response = requests.get(url)
    if response.status_code == 404 and response.text is not None:
        # 404 gives useful information, so we still want to parse it
        pass
    else:
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise WebRequestException(f'Failed to GET request to URL {url}. Error: {e}')

    try:
        soup = BeautifulSoup(response.text, 'lxml')
    except Exception as e:
        raise WebParseException(f'Failed to parse response using lxml. Error: {e}')

    # Search for synonyms
    try:
        # Parse meanings id
        meanings = soup.find('div', {'id': 'meanings'})
        if meanings is None:
            raise WebParseException('Failed to parse "id" of "meanings" from webpage.')

        # Parse container
        container = soup.find('div', {'data-testid': 'word-grid-container'})
        if container is None:
            raise WebParseException('Failed to parse "data-testid" of "word-grid-container" from meanings.')

        # Get synonyms
        synonyms = [span.get_text(strip=True) for span in container.find_all('a')]
        return (True, synonyms)
    except WebParseException as syn_err:
        # Search for suggestions
        try:
            # Parse spell suggestions div
            spell_sug = soup.find('div', {'class': 'spell-suggestions'})
            if spell_sug is None:
                raise WebParseException('Failed to parse "class" of "spell-suggestions" from webpage.')
            
            # Parse out all suggestions
            suggestions = [span.get_text(strip=True) for span in spell_sug.find_all('a')]
            return (False, suggestions)
        except WebParseException as sug_err:
            raise WebParseException(f'Failed to parse the webpage. Synonym parse error: {syn_err} Suggestion parse error: {sug_err}')
