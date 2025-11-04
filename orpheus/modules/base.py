from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Optional

from utils.models import DownloadTypeEnum, MediaIdentification, TrackInfo, AlbumInfo, PlaylistInfo, ArtistInfo, Tags


class DownloadModule(ABC):
    """
    Canonical interface that all service modules should implement.
    Existing modules can progressively adopt this contract; the orchestrator
    will emit warnings for missing capabilities.
    """

    service_name: str

    @abstractmethod
    def search(self, query_type: DownloadTypeEnum, query: str, track_info: Optional[TrackInfo] = None,
               limit: int = 10) -> Iterable[MediaIdentification]:
        raise NotImplementedError

    @abstractmethod
    def get_track_info(self, track_id: str, quality_tier, codec_options, **kwargs) -> TrackInfo:
        raise NotImplementedError

    @abstractmethod
    def get_track_download(self, track_id: str, **kwargs) -> Any:
        raise NotImplementedError

    def get_album_info(self, album_id: str, **kwargs) -> AlbumInfo:
        raise NotImplementedError

    def get_playlist_info(self, playlist_id: str, **kwargs) -> PlaylistInfo:
        raise NotImplementedError

    def get_artist_info(self, artist_id: str, **kwargs) -> ArtistInfo:
        raise NotImplementedError

    def get_track_tags(self, track_info: TrackInfo) -> Tags:
        return track_info.tags

    def module_capabilities(self) -> Dict[str, bool]:
        """
        Optional hook for modules to declare custom capabilities.
        """
        return {}


def has_contract_methods(module: Any) -> Dict[str, bool]:
    required_methods = [
        'get_track_info',
        'get_track_download'
    ]
    optional_methods = [
        'search',
        'get_album_info',
        'get_playlist_info',
        'get_artist_info',
        'get_track_tags'
    ]
    missing_required = [method for method in required_methods if not hasattr(module, method)]
    missing_optional = [method for method in optional_methods if not hasattr(module, method)]
    return {
        'missing_required': bool(missing_required),
        'missing_optional': bool(missing_optional),
        'has_contract': isinstance(module, DownloadModule)
    }
