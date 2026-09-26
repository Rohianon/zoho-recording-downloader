import pytest

from models import Recording
from services.recordings import matches
from tests.conftest import api_record

PATTERN = r"pydata\s*26h"


def parse(**overrides) -> Recording:
    return Recording.model_validate(api_record(**overrides) | {"tz": "Africa/Nairobi"})


@pytest.mark.parametrize(
    "topic, expected",
    [
        ("Pydata26H (2)", True),
        ("PyData 26h", True),
        ("26h Advanced Machine Learning", False),
        ("Introduction to Unsupervised Learning", False),
        ("Cohort 126H", False),
        ("Team standup", False),
    ],
)
def test_title_pattern(topic, expected):
    assert matches(parse(topic=topic), PATTERN) is expected


def test_parses_api_fields_and_coerces_meeting_key():
    rec = parse()
    assert rec.id == "e1"
    assert rec.meeting_key == "1087598854"
    assert rec.downloadable


def test_filename_uses_local_time_and_slug():
    assert parse(topic="Pydata26H (1)").filename == "2025-09-24_2012_pydata26h-1.mp4"
    assert parse(topic="  !!! ").filename.endswith("_recording.mp4")


def test_youtube_title_capped_at_100_chars():
    assert len(parse(topic="x" * 200).youtube_title) == 100


@pytest.mark.parametrize("overrides", [{"status": "PROCESSING"}, {"downloadUrl": ""}])
def test_not_downloadable_until_uploaded(overrides):
    assert not parse(**overrides).downloadable
