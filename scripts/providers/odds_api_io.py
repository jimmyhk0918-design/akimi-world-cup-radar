import os
import re
from datetime import datetime, timezone
from statistics import mean, pstdev
from typing import Dict, Iterable, List, Optional

from .http import get_json


class OddsApiIoProvider:
    BASE_URL = "https://api.odds-api.io/v3"

    def __init__(self, api_key: str = "", bookmakers: str = ""):
        self.api_key = api_key or os.getenv("ODDS_API_KEY", "")
        if not self.api_key:
            raise ValueError("ODDS_API_KEY is required")
        configured = bookmakers or os.getenv(
            "ODDS_BOOKMAKERS",
            "Bet365,Unibet,Betfair,Pinnacle",
        )
        self.bookmakers = ",".join(
            name.strip() for name in configured.split(",") if name.strip()
        )

    def fetch_events(self, date_from: str, date_to: str) -> List[Dict]:
        return get_json(
            "{}/events".format(self.BASE_URL),
            {
                "apiKey": self.api_key,
                "sport": "football",
                "status": "pending,live",
                "from": date_from,
                "to": date_to,
                "limit": 200,
            },
        )

    def fetch_odds(self, event_ids: Iterable[int]) -> List[Dict]:
        event_ids = list(event_ids)
        rows = []
        for start in range(0, len(event_ids), 10):
            batch = event_ids[start:start + 10]
            payload = get_json(
                "{}/odds/multi".format(self.BASE_URL),
                {
                    "apiKey": self.api_key,
                    "eventIds": ",".join(str(event_id) for event_id in batch),
                    "bookmakers": self.bookmakers,
                },
            )
            rows.extend(payload)
        return rows


def normalize_team_name(value: str) -> str:
    aliases = {
        "unitedstates": "usa",
        "unitedstatesofamerica": "usa",
        "korearepublic": "southkorea",
        "republicofkorea": "southkorea",
        "czechia": "czechrepublic",
        "ivorycoast": "cotedivoire",
        "drcongo": "congodr",
        "democraticrepublicofcongo": "congodr",
        "curacao": "curacao",
    }
    normalized = re.sub(r"[^a-z0-9]", "", value.lower())
    return aliases.get(normalized, normalized)


def event_key(home: str, away: str) -> str:
    return "{}|{}".format(normalize_team_name(home), normalize_team_name(away))


def match_events(events: List[Dict]) -> Dict[str, Dict]:
    matched = {}
    for event in events:
        home = event.get("home", "")
        away = event.get("away", "")
        if home and away:
            matched[event_key(home, away)] = event
    return matched


def _decimal(value) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 1 else None


def parse_event_odds(event: Dict) -> Optional[Dict]:
    bookmaker_rows = []
    updated_times = []
    for bookmaker, markets in event.get("bookmakers", {}).items():
        for market in markets:
            if market.get("name", "").upper() not in ("ML", "MONEYLINE", "1X2"):
                continue
            for row in market.get("odds", []):
                home = _decimal(row.get("home"))
                draw = _decimal(row.get("draw"))
                away = _decimal(row.get("away"))
                if not all((home, draw, away)):
                    continue
                implied = {
                    "home": 1 / home,
                    "draw": 1 / draw,
                    "away": 1 / away,
                }
                total = sum(implied.values())
                bookmaker_rows.append({
                    "bookmaker": bookmaker,
                    "odds": {"home": home, "draw": draw, "away": away},
                    "probabilities": {
                        key: value / total for key, value in implied.items()
                    },
                })
                if market.get("updatedAt"):
                    updated_times.append(market["updatedAt"])
                break
            break

    if not bookmaker_rows:
        return None

    probabilities = {
        outcome: mean(row["probabilities"][outcome] for row in bookmaker_rows)
        for outcome in ("home", "draw", "away")
    }
    average_odds = {
        outcome: mean(row["odds"][outcome] for row in bookmaker_rows)
        for outcome in ("home", "draw", "away")
    }
    home_values = [row["probabilities"]["home"] for row in bookmaker_rows]
    dispersion = pstdev(home_values) if len(home_values) > 1 else 0
    updated_at = max(updated_times) if updated_times else datetime.now(timezone.utc).isoformat()
    return {
        "event_id": event.get("id"),
        "probabilities": probabilities,
        "odds": average_odds,
        "bookmaker_count": len(bookmaker_rows),
        "bookmakers": [row["bookmaker"] for row in bookmaker_rows],
        "dispersion": dispersion,
        "updated_at": updated_at,
    }
