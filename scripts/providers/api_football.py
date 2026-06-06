import os
from typing import Dict, List

from .base import FixtureProvider, LiveDataProvider
from .http import get_json


class ApiFootballProvider(FixtureProvider, LiveDataProvider):
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY", "")
        if not self.api_key:
            raise ValueError("API_FOOTBALL_KEY is required")

    @property
    def headers(self) -> Dict[str, str]:
        return {"x-apisports-key": self.api_key}

    def fetch_fixtures(self) -> List[Dict]:
        payload = get_json(
            "{}/fixtures".format(self.BASE_URL),
            {"league": 1, "season": 2026},
            self.headers,
        )
        return payload.get("response", [])

    def fetch_live_state(self, match_id: str) -> Dict:
        payload = get_json(
            "{}/fixtures".format(self.BASE_URL),
            {"id": match_id},
            self.headers,
        )
        rows = payload.get("response", [])
        return rows[0] if rows else {}
