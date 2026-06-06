from abc import ABC, abstractmethod
from typing import Dict, List


class FixtureProvider(ABC):
    @abstractmethod
    def fetch_fixtures(self) -> List[Dict]:
        raise NotImplementedError


class OddsProvider(ABC):
    @abstractmethod
    def fetch_match_odds(self, match_id: str) -> Dict:
        raise NotImplementedError


class LiveDataProvider(ABC):
    @abstractmethod
    def fetch_live_state(self, match_id: str) -> Dict:
        raise NotImplementedError
