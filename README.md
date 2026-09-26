# zoho-downloader

Pulls Zindua class recordings (e.g. PyData 26H) out of Zoho Meeting to local disk.
`data/recordings/manifest.json` tracks what's downloaded and holds a ready-made YouTube
title/description per video for a later upload step.

```
main.py        CLI entry point (list / download)
models/        pydantic models: Settings, Recording, ManifestEntry
services/      zoho_meeting (API client), recordings (filter + download), manifest
scripts/       one-off tools: get_refresh_token.py
data/          gitignored output: data/recordings/*.mp4 + manifest.json
tests/         pytest, Zoho HTTP mocked with `responses` — `uv run pytest`
```

## Setup

1. https://api-console.zoho.com → **Add Client → Self Client**. Copy the client ID/secret into `.env` (see `.env.example`).
2. `make scopes` prints the scopes — paste them into the Self Client's **Generate Code** tab, pick the Zindua Meeting org, and copy the grant code.
3. `make token CODE=<grant-code>` → put the printed `ZOHO_REFRESH_TOKEN` in `.env`.

## Use

```sh
make                     # list all commands
make list-all            # everything in the org — check titles
make list                # only TITLE_PATTERN matches (✓ = on disk)
make dry-run
make download            # resumable, skips what's already downloaded
make download PATTERN='pandas'   # one-off regex override
make test
```

Tune `TITLE_PATTERN` in `.env` or pass `PATTERN=...` to change what counts as a class recording.
