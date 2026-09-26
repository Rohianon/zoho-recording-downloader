"""Fetch, filter and download recordings."""

import re

from models import Recording, Settings

from .manifest import Manifest
from .zoho_meeting import ZohoError, ZohoMeeting


def matches(rec: Recording, pattern: str) -> bool:
    return re.search(pattern, rec.topic, re.IGNORECASE) is not None


def fetch(client: ZohoMeeting, settings: Settings, pattern: str | None = None) -> list[Recording]:
    recs = [Recording.model_validate({**r, "tz": settings.timezone}) for r in client.recordings()]
    recs.sort(key=lambda r: r.start_ms)
    return [r for r in recs if pattern is None or matches(r, pattern)]


def download_all(client: ZohoMeeting, recs: list[Recording], manifest: Manifest, dry_run: bool = False) -> int:
    """Download recordings not already on disk. Returns the number of failures."""
    pending = [r for r in recs if not manifest.is_downloaded(r)]
    print(f"{len(recs)} matching, {len(recs) - len(pending)} already downloaded, {len(pending)} to fetch")

    failures = 0
    for r in pending:
        if not r.downloadable:
            print(f"  skip  {r.topic} (status={r.status or 'unknown'}, no download URL yet)")
            continue
        print(f"  get   {r.filename}  ({r.size})")
        if dry_run:
            continue

        def progress(done, total):
            pct = f"{done * 100 // total:3d}%" if total else ""
            print(f"\r        {done / 1e6:8.1f} MB {pct}", end="", flush=True)

        try:
            client.download(r.download_url, manifest.root / r.filename, on_progress=progress)
            print()
            manifest.record(r)
        except (ZohoError, OSError) as e:
            print(f"\n  FAIL  {r.topic}: {e}")
            failures += 1
    return failures
