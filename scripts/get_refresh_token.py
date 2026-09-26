"""One-time setup: swap a Zoho Self Client grant code for a refresh token.

    uv run scripts/get_refresh_token.py            # prints the scopes to request
    uv run scripts/get_refresh_token.py <code>     # prints ZOHO_REFRESH_TOKEN for .env
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests  # noqa: E402

from models import SCOPES, Settings  # noqa: E402

if len(sys.argv) != 2:
    print(f"Scopes to paste into the Self Client 'Generate Code' tab:\n\n{SCOPES}\n")
    sys.exit(__doc__)

s = Settings()
data = requests.post(
    f"{s.accounts_url}/oauth/v2/token",
    data={
        "grant_type": "authorization_code",
        "client_id": s.zoho_client_id,
        "client_secret": s.zoho_client_secret,
        "code": sys.argv[1],
    },
    timeout=30,
).json()
if "refresh_token" not in data:
    sys.exit(f"Token exchange failed: {data}")
print(f"Add this to your .env:\n\nZOHO_REFRESH_TOKEN={data['refresh_token']}")
