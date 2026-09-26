import pytest
import responses

from services.zoho_meeting import ZohoError, ZohoMeeting
from tests.conftest import api_record

TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
LIST_URL = "https://meeting.zoho.com/meeting/api/v2/123/recordings.json"
DL_URL = "https://download.zoho.com/webdownload?event-id=e1"


@pytest.fixture
def api():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.post(TOKEN_URL, json={"access_token": "tok", "expires_in": 3600})
        yield rsps


def test_access_token_is_cached(api, settings):
    api.get(LIST_URL, json={"recordings": [], "meta": {"moreRecords": False}})
    client = ZohoMeeting(settings)
    list(client.recordings())
    list(client.recordings())
    assert sum(c.request.url == TOKEN_URL for c in api.calls) == 1
    assert api.calls[-1].request.headers["Authorization"] == "Zoho-oauthtoken tok"


def test_bad_refresh_token_raises(settings):
    with responses.RequestsMock() as rsps:
        rsps.post(TOKEN_URL, json={"error": "invalid_code"})
        with pytest.raises(ZohoError, match="invalid_code"):
            list(ZohoMeeting(settings).recordings())


def test_paginates_and_dedupes(api, settings):
    page1 = {"recordings": [api_record(erecordingId="a"), api_record(erecordingId="b")], "meta": {"moreRecords": True}}
    page2 = {"recordings": [api_record(erecordingId="b"), api_record(erecordingId="c")], "meta": {"moreRecords": False}}
    api.get(LIST_URL, json=page1)
    api.get(LIST_URL, json=page2)
    ids = [r["erecordingId"] for r in ZohoMeeting(settings).recordings()]
    assert ids == ["a", "b", "c"]


def test_pagination_stops_when_server_ignores_index(api, settings):
    page = {"recordings": [api_record(erecordingId="a")], "meta": {"moreRecords": True}}
    api.get(LIST_URL, json=page)  # same page forever
    assert [r["erecordingId"] for r in ZohoMeeting(settings).recordings()] == ["a"]


def test_zsoid_looked_up_when_not_configured(api, settings):
    settings.zoho_zsoid = None
    api.get("https://meeting.zoho.com/api/v2/user.json", json={"userDetails": {"zsoid": 123}})
    api.get(LIST_URL, json={"recordings": [], "meta": {}})
    assert list(ZohoMeeting(settings).recordings()) == []


def test_download_writes_file(api, settings, tmp_path):
    api.get(DL_URL, body=b"x" * 10, content_type="video/mp4")
    dest = tmp_path / "v.mp4"
    ZohoMeeting(settings).download(DL_URL, dest)
    assert dest.read_bytes() == b"x" * 10
    assert not dest.with_suffix(".mp4.part").exists()


def test_download_resumes_from_part_file(api, settings, tmp_path):
    dest = tmp_path / "v.mp4"
    dest.with_suffix(".mp4.part").write_bytes(b"abc")
    api.get(DL_URL, body=b"def", status=206, content_type="video/mp4")
    ZohoMeeting(settings).download(DL_URL, dest)
    assert dest.read_bytes() == b"abcdef"
    assert api.calls[-1].request.headers["Range"] == "bytes=3-"


def test_download_restarts_if_range_ignored(api, settings, tmp_path):
    dest = tmp_path / "v.mp4"
    dest.with_suffix(".mp4.part").write_bytes(b"stale")
    api.get(DL_URL, body=b"full", status=200, content_type="video/mp4")
    ZohoMeeting(settings).download(DL_URL, dest)
    assert dest.read_bytes() == b"full"


def test_download_rejects_html_login_page(api, settings, tmp_path):
    api.get(DL_URL, body="<html>sign in</html>", content_type="text/html")
    with pytest.raises(ZohoError, match="Expected video"):
        ZohoMeeting(settings).download(DL_URL, tmp_path / "v.mp4")


def test_download_creates_missing_directory(api, settings, tmp_path):
    api.get(DL_URL, body=b"x", content_type="video/mp4")
    dest = tmp_path / "recordings" / "v.mp4"
    ZohoMeeting(settings).download(DL_URL, dest)
    assert dest.read_bytes() == b"x"
