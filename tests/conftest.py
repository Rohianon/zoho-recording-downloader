import pytest

from models import Settings


@pytest.fixture
def settings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # keep any real .env out of the tests
    return Settings(
        zoho_client_id="cid",
        zoho_client_secret="secret",
        zoho_refresh_token="refresh",
        zoho_zsoid="123",
        download_dir=tmp_path / "recordings",
    )


def api_record(**overrides) -> dict:
    """A recording as returned by recordings.json (trimmed from Zoho's docs sample)."""
    rec = {
        "erecordingId": "e1",
        "topic": "Pydata26H (1)",
        "startTimeinMs": 1758733920000,  # Wed 24 Sep 2025 20:12 EAT
        "durationInMins": 80,
        "fileSize": "506 MB",
        "meetingKey": 1087598854,
        "downloadUrl": "https://download.zoho.com/webdownload?event-id=e1",
        "status": "UPLOADED",
    }
    return rec | overrides
