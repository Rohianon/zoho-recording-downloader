"""Manifest entries: what's on disk, plus the slot a YouTube upload step fills in."""

from datetime import datetime

from pydantic import BaseModel


class YouTubeMeta(BaseModel):
    title: str
    description: str
    video_id: str | None = None
    uploaded_at: datetime | None = None


class ManifestEntry(BaseModel):
    topic: str
    start: datetime
    duration_mins: int
    meeting_key: str
    file: str
    bytes: int
    downloaded_at: datetime
    youtube: YouTubeMeta
