from typing import Dict, List

from .base import FixtureProvider
from .http import get_json


class OpenFootballProvider(FixtureProvider):
    URL = "https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json"

    def fetch_fixtures(self) -> List[Dict]:
        payload = get_json(self.URL)
        return payload.get("matches", [])
