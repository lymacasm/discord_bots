class ScraperException(Exception):
    """ Base scraper exception for all scrapers. """
    pass

class RequestException(ScraperException):
    """ Base web request exception for all scrapers. """
    pass

class ParseException(ScraperException):
    """ Base parsing error exception for all scrapers. """
    pass

class SuggestionException(ScraperException):
    def __init__(self, suggestions: list[str]):
        self.suggestions = suggestions

    def __str__(self):
        return ", ".join(self.suggestions)