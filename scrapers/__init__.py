class ScraperException(Exception):
    """ Base scraper exception for all scrapers. """
    pass

class RequestException(ScraperException):
    """ Base web request exception for all scrapers. """
    pass

class ParseException(ScraperException):
    """ Base parsing error exception for all scrapers. """
    pass