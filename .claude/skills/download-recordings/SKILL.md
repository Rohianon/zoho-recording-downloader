---
name: download-recordings
description: Run the zoho-downloader pipeline to find and download Zindua class recordings (e.g. PyData 26H) from Zoho Meeting to data/recordings/. Use when asked to fetch, sync, list or check class recordings, or to debug why a recording didn't download.
---

# Download class recordings

Pipeline: Zoho Meeting API → filter by topic regex → `data/recordings/*.mp4` + `data/recordings/manifest.json`.

## Steps

1. Check `.env` exists with `ZOHO_CLIENT_ID`, `ZOHO_CLIENT_SECRET`, `ZOHO_REFRESH_TOKEN`.
   Never print their values. If the refresh token is missing, tell the user to run
   `uv run scripts/get_refresh_token.py` (prints scopes) and then
   `uv run scripts/get_refresh_token.py <grant-code>` — the grant code comes from the
   Zoho API console and only the user can get it.
2. `uv run main.py list --all` — every recording in the org. Compare against what the
   user expects; if class sessions are missing from the filtered list, suggest a wider
   `TITLE_PATTERN` (or `--pattern`) rather than silently changing `.env`.
3. `uv run main.py download --dry-run`, show the plan, then `uv run main.py download`.
   Downloads are large (hundreds of MB to ~1 GB each) — run in the background for
   more than a couple of files. Re-running is safe: finished files are skipped and
   `.part` files resume.
4. Report: what was downloaded, skipped (status not `UPLOADED`), and failed.

## Troubleshooting

- `Could not refresh access token` → refresh token revoked/expired or wrong `ZOHO_DC`.
- 401/403 on `recordings.json` → missing `ZohoMeeting.recording.READ` scope, or the
  account's plan/licence doesn't allow API access.
- Download returns HTML/JSON instead of video → missing
  `ZohoMeeting.meetinguds.READ,ZohoFiles.files.READ` scopes, or the download host
  rejects the OAuth header; inspect `downloadUrl` from `list --json`.
- Fewer recordings than the web UI → pagination (undocumented; see
  `services/zoho_meeting.py:recordings`). Check `meta.moreRecords` in a raw response.

## manifest.json

Keyed by `erecordingId`. Each entry's `youtube` block (`title`, `description`,
`video_id`, `uploaded_at`) is the hand-off to the future Zindua School YouTube upload
stage — preserve existing `youtube` values when editing entries.
