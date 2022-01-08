from tracking.sprint import SprintTracker, SprintError
from tracking.sprint.sql import SprintTrackingSQL

class SprintTrackingTypeError(SprintError):
    pass

class TrackingTypes:
    SQL = 'SQL'

def tracking_factory(track_type : TrackingTypes, *args, **kwargs) -> SprintTracker:
    if track_type == TrackingTypes.SQL:
        return SprintTrackingSQL(*args, **kwargs)
    raise SprintTrackingTypeError(f'Unknown tracking type of {track_type}.')
