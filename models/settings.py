"""App settings, read from environment / .env."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Zoho data centres: accounts + meeting hosts differ per region.
DATA_CENTRES = {
    "com": ("https://accounts.zoho.com", "https://meeting.zoho.com"),
    "eu": ("https://accounts.zoho.eu", "https://meeting.zoho.eu"),
    "in": ("https://accounts.zoho.in", "https://meeting.zoho.in"),
    "com.au": ("https://accounts.zoho.com.au", "https://meeting.zoho.com.au"),
    "jp": ("https://accounts.zoho.jp", "https://meeting.zoho.jp"),
}

SCOPES = ",".join(
    [
        "ZohoMeeting.manageOrg.READ",  # user.json -> zsoid
        "ZohoMeeting.recording.READ",  # list recordings
        "ZohoMeeting.meetinguds.READ",  # download recordings
        "ZohoFiles.files.READ",
    ]
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    zoho_client_id: str
    zoho_client_secret: str
    zoho_refresh_token: str | None = None
    zoho_dc: str = Field("com", pattern="^(com|eu|in|com\\.au|jp)$")
    zoho_zsoid: str | None = None
    download_dir: Path = Path("data/recordings")
    title_pattern: str = r"pydata\s*26h"
    timezone: str = "Africa/Nairobi"

    @property
    def accounts_url(self) -> str:
        return DATA_CENTRES[self.zoho_dc][0]

    @property
    def meeting_url(self) -> str:
        return DATA_CENTRES[self.zoho_dc][1]
