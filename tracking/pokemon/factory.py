from tracking.pokemon import _PokemonTrackingBase, PokemonTrackingException
from tracking.pokemon.files import PokemonTrackingFiles
from tracking.pokemon.sql import PokemonTrackingSQL

class PokemonTrackingTypeError(PokemonTrackingException):
    pass

class TrackingTypes:
    FILES = 'FILES'
    SQL = 'SQL'

def tracking_factory(track_type : TrackingTypes) -> _PokemonTrackingBase:
    if track_type == TrackingTypes.FILES:
        return PokemonTrackingFiles()
    elif track_type == TrackingTypes.SQL:
        return PokemonTrackingSQL()
    raise PokemonTrackingException(f'Unknown tracking type of {track_type}.')
