from dataclasses import dataclass
from typing import Dict

from utils.models import TrackInfo, Tags


@dataclass
class NormalizedTrack:
    name: str
    album: str
    artists: str
    codec: str
    duration: int
    metadata: Dict[str, str]


class MetadataNormalizer:
    def normalize_track(self, track_info: TrackInfo) -> NormalizedTrack:
        artists = ', '.join(track_info.artists)
        codec = track_info.codec.name if track_info.codec else 'UNKNOWN'
        duration = track_info.duration or 0
        metadata = {
            'release_year': str(track_info.release_year) if track_info.release_year else '',
            'explicit': 'yes' if track_info.explicit else 'no'
        }
        metadata.update(self._tags_to_dict(track_info.tags))
        return NormalizedTrack(
            name=track_info.name,
            album=track_info.album,
            artists=artists,
            codec=codec,
            duration=duration,
            metadata=metadata
        )

    @staticmethod
    def _tags_to_dict(tags: Tags) -> Dict[str, str]:
        result = {}
        if not tags:
            return result
        for field in ['album_artist', 'composer', 'track_number', 'total_tracks', 'disc_number', 'total_discs', 'label']:
            value = getattr(tags, field, None)
            if value:
                result[field] = str(value)
        return result


metadata_normalizer = MetadataNormalizer()
