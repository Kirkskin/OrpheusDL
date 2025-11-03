import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from orpheus.core import Orpheus
from utils.models import (
    CodecEnum,
    DownloadEnum,
    DownloadTypeEnum,
    ModuleInformation,
    ModuleModes,
    Oprinter,
    Tags,
    TrackInfo,
    TrackDownloadInfo,
)
from orpheus.music_downloader import Downloader
from orpheus.tagging import tag_file, ContainerEnum


class FakeService:
    def __init__(self, track_info):
        self._track_info = track_info

    def get_track_info(self, track_id, quality_tier, codec_options, **extra_kwargs):
        return self._track_info

    def get_track_download(self, **download_kwargs):
        return TrackDownloadInfo(
            download_type=DownloadEnum.URL,
            file_url="https://example.invalid/track",
            file_url_headers={},
        )

    def get_track_lyrics(self, *args, **kwargs):
        return SimpleNamespace(embedded=None, synced=None)

    def get_track_credits(self, *args, **kwargs):
        return []


class DownloaderConversionTests(unittest.TestCase):
    def setUp(self):
        from utils.models import TrackInfo

        self.tempdir = tempfile.TemporaryDirectory()
        self.tags = Tags(
            track_number=1,
            total_tracks=1,
            disc_number=None,
            total_discs=None,
            comment=None,
        )
        self.track_info = TrackInfo(
            name="Test Track",
            album="Test Album",
            album_id="album123",
            artists=["Test Artist"],
            tags=self.tags,
            codec=CodecEnum.MP3,
            cover_url="",
            release_year=2024,
            duration=120,
            explicit=False,
            artist_id="artist123",
            animated_cover_url=None,
            description=None,
            bitrate=320,
            download_extra_kwargs={},
            cover_extra_kwargs={},
            credits_extra_kwargs={},
            lyrics_extra_kwargs={},
        )
        module_info = ModuleInformation(
            service_name="Test Service",
            module_supported_modes=ModuleModes.download,
        )
        self.global_settings = {
            "general": {"download_quality": "hifi"},
            "codecs": {"spatial_codecs": False, "proprietary_codecs": False},
            "formatting": {
                "force_album_format": False,
                "single_full_path_format": "{name}",
                "track_filename_format": "{track_number}. {name}",
                "album_format": "{name}",
                "enable_zfill": False,
            },
            "covers": {
                "embed_cover": False,
                "main_compression": "high",
                "main_resolution": 1400,
                "save_external": False,
                "external_format": "jpg",
                "external_compression": "low",
                "external_resolution": 3000,
                "save_animated_cover": False,
            },
            "lyrics": {
                "embed_lyrics": False,
                "embed_synced_lyrics": False,
                "save_synced_lyrics": False,
            },
            "playlist": {
                "save_m3u": False,
                "paths_m3u": "absolute",
                "extended_m3u": False,
            },
            "module_defaults": {
                "lyrics": "default",
                "covers": "default",
                "credits": "default",
            },
            "advanced": {
                "ignore_different_artists": True,
                "codec_conversions": {"mp3": "aac"},
                "conversion_flags": {},
                "conversion_keep_original": False,
                "cover_variance_threshold": 8,
                "debug_mode": False,
                "disable_subscription_checks": False,
                "enable_undesirable_conversions": False,
                "ignore_existing_files": False,
            },
        }
        module_controls = {
            "module_list": [],
            "module_settings": {"test": module_info},
            "loaded_modules": {"test": FakeService(self.track_info)},
            "module_loader": lambda name: None,
        }
        self.downloader = Downloader(
            self.global_settings, module_controls, Oprinter(), self.tempdir.name
        )
        self.downloader.download_mode = DownloadTypeEnum.track
        self.downloader.third_party_modules = {
            ModuleModes.covers: None,
            ModuleModes.lyrics: None,
            ModuleModes.credits: None,
        }
        self.downloader.service = module_controls["loaded_modules"]["test"]
        self.downloader.service_name = "test"

    def tearDown(self):
        self.tempdir.cleanup()

    @staticmethod
    def _fake_download_file(url, file_location, **kwargs):
        os.makedirs(os.path.dirname(file_location), exist_ok=True)
        with open(file_location, "wb") as fh:
            fh.write(b"dummy")

    def test_skips_lossy_conversion_when_disabled(self):
        cover_path = os.path.join(self.tempdir.name, "cover.jpg")
        with open(cover_path, "wb") as fh:
            fh.write(b"cover")

        with patch("orpheus.music_downloader.download_file", self._fake_download_file), patch(
            "orpheus.music_downloader.tag_file"
        ), patch("orpheus.music_downloader.os.path.isfile", return_value=False), patch(
            "orpheus.music_downloader.ffmpeg.input",
            side_effect=AssertionError("ffmpeg conversion unexpectedly triggered"),
        ):
            self.downloader.download_track(
                "track123",
                album_location=f"{self.tempdir.name}/",
                cover_temp_location=cover_path,
            )


class FakeEasyID3(dict):
    def __init__(self):
        super().__init__()
        self._EasyID3__id3 = SimpleNamespace(_DictProxy__dict={})

    def RegisterTextKey(self, *args, **kwargs):
        return None

    def RegisterTXXXKey(self, *args, **kwargs):
        return None


class FakeEasyMP3:
    def __init__(self, _file_path):
        self.tags = FakeEasyID3()

    def __setitem__(self, key, value):
        self.tags[key] = value

    def save(self, *args, **kwargs):
        return None


class TaggingCommentTests(unittest.TestCase):
    def test_mp3_comment_uses_comment_field(self):
        comment_text = "This is the comment"
        description_text = "Different description"
        from utils.models import TrackInfo

        tags = Tags(
            comment=comment_text,
            description=description_text,
            track_number=1,
            total_tracks=1,
        )
        track_info = TrackInfo(
            name="Test Track",
            album="Test Album",
            album_id="album1",
            artists=["Artist"],
            tags=tags,
            codec=CodecEnum.MP3,
            cover_url="",
            release_year=2024,
            duration=123,
            explicit=None,
            artist_id="artist1",
            download_extra_kwargs={},
            cover_extra_kwargs={},
            credits_extra_kwargs={},
            lyrics_extra_kwargs={},
        )
        comm_calls = []

        def fake_comm(encoding, lang, desc, text):
            comm_calls.append(
                {"encoding": encoding, "lang": lang, "desc": desc, "text": text}
            )
            return {"text": text}

        with patch("orpheus.tagging.EasyMP3", FakeEasyMP3), patch(
            "orpheus.tagging.EasyID3", FakeEasyID3
        ), patch("orpheus.tagging.COMM", fake_comm):
            tag_file(
                file_path=os.path.join(tempfile.gettempdir(), "dummy.mp3"),
                image_path=None,
                track_info=track_info,
                credits_list=[],
                embedded_lyrics=None,
                container=ContainerEnum.mp3,
            )

        self.assertTrue(comm_calls, "COMM frame was not written")
        self.assertEqual(comm_calls[0]["text"], comment_text)


class ModuleHealthCheckTests(unittest.TestCase):
    def setUp(self):
        self.orpheus = Orpheus.__new__(Orpheus)
        self.orpheus.module_list = {"fake"}
        self.orpheus.module_settings = {
            "fake": ModuleInformation(
                service_name="Fake",
                module_supported_modes=ModuleModes.download,
                test_url="https://fake.service/track/123",
            )
        }
        self.orpheus.settings = {
            "global": {
                "general": {"download_quality": "hifi"},
                "codecs": {"proprietary_codecs": False, "spatial_codecs": False},
                "artist_downloading": {"return_credited_albums": True},
            }
        }
        class FakeModule:
            def get_track_info(self, track_id, quality_tier, codec_options, **kwargs):
                tags = Tags(track_number=1, total_tracks=1)
                return TrackInfo(
                    name="Track",
                    album="Album",
                    album_id="album",
                    artists=["Artist"],
                    tags=tags,
                    codec=CodecEnum.MP3,
                    cover_url="",
                    release_year=2024,
                )

        self._fake_module = FakeModule()
        self.orpheus.load_module = lambda name: self._fake_module

    def test_health_check_passes_with_default_url_parsing(self):
        self.assertTrue(self.orpheus.run_module_health_check("fake"))


if __name__ == "__main__":
    unittest.main()
