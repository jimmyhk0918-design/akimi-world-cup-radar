import os
from typing import Dict, List

from .base import FixtureProvider
from .http import get_json


class FootballDataProvider(FixtureProvider):
    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_KEY", "")
        if not self.api_key:
            raise ValueError("FOOTBALL_DATA_KEY is required")

    def fetch_fixtures(self) -> List[Dict]:
        payload = get_json(
            "{}/competitions/WC/matches".format(self.BASE_URL),
            headers={"X-Auth-Token": self.api_key},
        )
        return payload.get("matches", [])
