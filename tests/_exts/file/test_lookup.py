from unittest import mock

import pytest

from mopidy import exceptions
from mopidy._lib import paths
from tests import path_to_data_dir


@pytest.mark.parametrize(
    "track_uri",
    [
        paths.path_to_uri(path_to_data_dir("song1.wav")),
    ],
)
def test_lookup(provider, track_uri):
    result = provider.lookup(track_uri)

    assert len(result) == 1
    track = result[0]
    assert track.uri == track_uri
    assert track.length == 4406
    assert track.name == "song1.wav"

    with mock.patch(
        "mopidy._exts.file.library.tags.convert_tags_to_track",
        side_effect=exceptions.ScannerError("test"),
    ):
        result = provider.lookup(track_uri)
        assert len(result) == 1
        track = result[0]
        assert track.uri == track_uri
        assert track.name == "song1.wav"


def test_lookup_with_invalid_tags(provider):
    """A file with tags we can't validate is still listed, just without tags."""
    track_uri = paths.path_to_uri(path_to_data_dir("song1.wav"))
    real_scan = provider._scanner.scan

    def scan_with_invalid_tags(uri, *args, **kwargs):
        result = real_scan(uri, *args, **kwargs)
        return result._replace(tags=result.tags | {"track-number": [-1]})

    with mock.patch.object(
        provider._scanner,
        "scan",
        side_effect=scan_with_invalid_tags,
    ):
        result = provider.lookup(track_uri)

    assert len(result) == 1
    assert result[0].uri == track_uri
    assert result[0].name == "song1.wav"
    assert result[0].track_no is None


def test_lookup_unwraps_pls_playlist(provider, tmp_path):
    pls_content = (
        "[playlist]\nNumberOfEntries=1\nFile1=http://stream.example.com/listen.pls\n"
    )
    pls_file = tmp_path / "test.pls"
    pls_file.write_text(pls_content)

    uri = f"file://{pls_file}"

    tracks = provider.lookup(uri)
    assert len(tracks) == 1
    assert tracks[0].uri == "http://stream.example.com/listen.pls"


def test_lookup_unwraps_m3u_playlist(provider, tmp_path):
    m3u_content = "http://stream.example.com/listen.mp3\n"
    m3u_file = tmp_path / "test.m3u"
    m3u_file.write_text(m3u_content)

    uri = f"file://{m3u_file}"

    tracks = provider.lookup(uri)
    assert len(tracks) == 1
    assert tracks[0].uri == "http://stream.example.com/listen.mp3"
