from tracking.pokemon import _PokemonTrackingBase, PokemonTrackingException
from tracking.pokemon.files import PokemonTrackingFiles

class PokemonTrackingTypeError(PokemonTrackingException):
    pass

class TrackingTypes:
    FILES = 'FILES'

def tracking_factory(track_type : TrackingTypes) -> _PokemonTrackingBase:
    if track_type == TrackingTypes.FILES:
        return PokemonTrackingFiles()
    raise PokemonTrackingException(f'Unknown tracking type of {track_type}.')