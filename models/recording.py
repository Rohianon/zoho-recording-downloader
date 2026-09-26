"""A Zoho Meeting recording, parsed from the recordings.json API."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Recording(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True, populate_by_name=True)

    id: str = Field(alias="erecordingId")
    topic: str = "untitled"
    start_ms: int = Field(0, alias="startTimeinMs")
    duration_mins: int = Field(0, alias="durationInMins")
    size: str = Field("?", alias="fileSize")
    meeting_key: str = Field("", alias="meetingKey")
    download_url: str = Field("", alias="downloadUrl")
    status: str = ""
    tz: str = "Africa/Nairobi"

    @property
    def start(self) -> datetime:
        from zoneinfo import ZoneInfo

        return datetime.fromtimestamp(self.start_ms / 1000, ZoneInfo(self.tz))

    @property
    def filename(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", self.topic.lower()).strip("-")[:80] or "recording"
        return f"{self.start:%Y-%m-%d_%H%M}_{slug}.mp4"

    @property
    def youtube_title(self) -> str:
        return f"{self.topic} | {self.start:%d %b %Y}"[:100]  # YouTube caps titles at 100 chars

    @property
    def downloadable(self) -> bool:
        return bool(self.download_url) and self.status in ("UPLOADED", "")
