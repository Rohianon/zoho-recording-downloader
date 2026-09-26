from models import Recording
from services.manifest import Manifest
from tests.conftest import api_record


def test_record_roundtrip_and_preserves_youtube_state(tmp_path):
    rec = Recording.model_validate(api_record())
    (tmp_path / rec.filename).write_bytes(b"video")

    Manifest(tmp_path).record(rec)
    m = Manifest(tmp_path)
    assert m.is_downloaded(rec)
    assert m.entries[rec.id].bytes == 5

    # A later upload stage fills in video_id; re-recording must not wipe it.
    m.entries[rec.id].youtube.video_id = "yt123"
    m.save()
    Manifest(tmp_path).record(rec)
    assert Manifest(tmp_path).entries[rec.id].youtube.video_id == "yt123"


def test_missing_file_means_not_downloaded(tmp_path):
    rec = Recording.model_validate(api_record())
    (tmp_path / rec.filename).write_bytes(b"video")
    Manifest(tmp_path).record(rec)
    (tmp_path / rec.filename).unlink()
    assert not Manifest(tmp_path).is_downloaded(rec)
