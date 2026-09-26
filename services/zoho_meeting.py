"""Thin Zoho Meeting API client: OAuth refresh, org lookup, recordings, download."""

import time
from collections.abc import Iterator
from pathlib import Path

import requests

from models import Settings


class ZohoError(RuntimeError):
    pass


class ZohoMeeting:
    def __init__(self, settings: Settings):
        if not settings.zoho_refresh_token:
            raise SystemExit("No ZOHO_REFRESH_TOKEN yet — run `uv run scripts/get_refresh_token.py <grant-code>` first.")
        self.s = settings
        self.session = requests.Session()
        self._token: str | None = None
        self._token_expiry = 0.0
        self._zsoid = settings.zoho_zsoid

    # --- auth -------------------------------------------------------------

    def _access_token(self) -> str:
        if self._token and time.time() < self._token_expiry - 60:
            return self._token
        resp = requests.post(
            f"{self.s.accounts_url}/oauth/v2/token",
            data={
                "grant_type": "refresh_token",
                "client_id": self.s.zoho_client_id,
                "client_secret": self.s.zoho_client_secret,
                "refresh_token": self.s.zoho_refresh_token,
            },
            timeout=30,
        )
        data = resp.json()
        if "access_token" not in data:
            raise ZohoError(f"Could not refresh access token: {data}")
        self._token = data["access_token"]
        self._token_expiry = time.time() + int(data.get("expires_in", 3600))
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Zoho-oauthtoken {self._access_token()}"}

    def _get_json(self, url: str, **params) -> dict:
        resp = self.session.get(url, headers=self._headers(), params=params or None, timeout=60)
        if resp.status_code >= 400:
            raise ZohoError(f"GET {url} -> {resp.status_code}: {resp.text[:500]}")
        return resp.json()

    # --- api --------------------------------------------------------------

    @property
    def zsoid(self) -> str:
        if not self._zsoid:
            data = self._get_json(f"{self.s.meeting_url}/api/v2/user.json")
            self._zsoid = str(data["userDetails"]["zsoid"])
        return self._zsoid

    def recordings(self) -> Iterator[dict]:
        """Yield every recording in the org, de-duplicated by erecordingId.

        Pagination isn't documented; when meta.moreRecords is true we try the
        `index` param Zoho uses elsewhere and stop as soon as a page adds nothing new.
        """
        url = f"{self.s.meeting_url}/meeting/api/v2/{self.zsoid}/recordings.json"
        seen: set[str] = set()
        index = 1
        while True:
            data = self._get_json(url, index=index) if index > 1 else self._get_json(url)
            page = data.get("recordings", [])
            new = [r for r in page if r.get("erecordingId") not in seen]
            for rec in new:
                seen.add(rec["erecordingId"])
                yield rec
            if not new or not data.get("meta", {}).get("moreRecords"):
                return
            index += len(page)

    def download(self, url: str, dest: Path, on_progress=None) -> None:
        """Stream a recording to dest via a .part file, resuming if one exists."""
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_suffix(dest.suffix + ".part")
        headers = self._headers()
        have = part.stat().st_size if part.exists() else 0
        if have:
            headers["Range"] = f"bytes={have}-"
        with self.session.get(url, headers=headers, stream=True, timeout=120) as resp:
            if resp.status_code == 416:  # .part already complete
                part.rename(dest)
                return
            if resp.status_code >= 400:
                raise ZohoError(f"Download failed {resp.status_code}: {resp.text[:300]}")
            ctype = resp.headers.get("Content-Type", "")
            if "json" in ctype or "html" in ctype:
                raise ZohoError(f"Expected video, got {ctype}: {resp.text[:300]}")
            if resp.status_code != 206:
                have = 0  # server ignored Range; start over
            total = have + int(resp.headers.get("Content-Length", 0))
            with open(part, "ab" if have else "wb") as fh:
                done = have
                for chunk in resp.iter_content(chunk_size=1 << 20):
                    fh.write(chunk)
                    done += len(chunk)
                    if on_progress:
                        on_progress(done, total)
        part.rename(dest)
