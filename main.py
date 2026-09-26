"""Pull Zindua class recordings (e.g. PyData 26H) out of Zoho Meeting."""

import argparse
import json
import sys

from pydantic import ValidationError

from models import Settings
from services.manifest import Manifest
from services.recordings import download_all, fetch
from services.zoho_meeting import ZohoError, ZohoMeeting


def cmd_list(args, settings: Settings) -> None:
    pattern = None if args.all else (args.pattern or settings.title_pattern)
    recs = fetch(ZohoMeeting(settings), settings, pattern)
    if args.json:
        json.dump([r.model_dump(by_alias=True) for r in recs], sys.stdout, indent=2)
        return
    manifest = Manifest(settings.download_dir)
    for r in recs:
        mark = "✓" if manifest.is_downloaded(r) else " "
        print(f"{mark} {r.start:%a %d %b %Y %H:%M}  {r.duration_mins:>4}m  {r.size:>8}  {r.status:<9} {r.topic}")
    print(f"\n{len(recs)} recording(s)" + (f" matching /{pattern}/i" if pattern else ""))


def cmd_download(args, settings: Settings) -> None:
    client = ZohoMeeting(settings)
    recs = fetch(client, settings, args.pattern or settings.title_pattern)
    if download_all(client, recs, Manifest(settings.download_dir), dry_run=args.dry_run):
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="list recordings (filtered by TITLE_PATTERN unless --all)")
    p.add_argument("-a", "--all", action="store_true", help="show every recording, no filter")
    p.add_argument("-p", "--pattern", help="regex to match against topic (case-insensitive)")
    p.add_argument("--json", action="store_true", help="dump parsed records as JSON")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("download", help="download matching recordings not yet on disk")
    p.add_argument("-p", "--pattern", help="regex to match against topic (case-insensitive)")
    p.add_argument("-n", "--dry-run", action="store_true")
    p.set_defaults(func=cmd_download)

    args = parser.parse_args()
    try:
        settings = Settings()
    except ValidationError as e:
        sys.exit(f"Bad or missing settings — copy .env.example to .env and fill it in.\n{e}")
    try:
        args.func(args, settings)
    except ZohoError as e:
        sys.exit(f"error: {e}")


if __name__ == "__main__":
    main()
