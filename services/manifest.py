"""data/recordings/manifest.json: what's downloaded, and the hand-off to later stages
(e.g. uploading to the Zindua School YouTube channel)."""

import json
from datetime import datetime
from pathlib import Path

from models import ManifestEntry, Recording, YouTubeMeta


class Manifest:
    def __init__(self, root: Path):
        self.root = root
        self.path = root / "manifest.json"
        raw = json.loads(self.path.read_text()) if self.path.exists() else {}
        self.entries = {k: ManifestEntry.model_validate(v) for k, v in raw.items()}

    def is_downloaded(self, rec: Recording) -> bool:
        entry = self.entries.get(rec.id)
        return bool(entry and (self.root / entry.file).exists())

    def record(self, rec: Recording) -> None:
        prev = self.entries.get(rec.id)
        self.entries[rec.id] = ManifestEntry(
            topic=rec.topic,
            start=rec.start,
            duration_mins=rec.duration_mins,
            meeting_key=rec.meeting_key,
            file=rec.filename,
            bytes=(self.root / rec.filename).stat().st_size,
            downloaded_at=datetime.now().astimezone(),
            youtube=prev.youtube
            if prev
            else YouTubeMeta(
                title=rec.youtube_title,
                description=f"{rec.topic}\nRecorded live {rec.start:%A %d %B %Y, %H:%M} (EAT).\nZindua School",
            ),
        )
        self.save()

    def save(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        data = {k: v.model_dump(mode="json") for k, v in self.entries.items()}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        tmp.replace(self.path)
