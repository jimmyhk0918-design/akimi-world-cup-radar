from math import exp, factorial, log
from typing import Dict, List


def normalize(probs: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, value) for value in probs.values())
    if total <= 0:
        raise ValueError("Probability total must be positive")
    return {key: max(0.0, value) / total for key, value in probs.items()}


def elo_expected_score(rating_a: float, rating_b: float) -> float:
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def elo_to_1x2(home_elo: float, away_elo: float, draw_base: float = 0.26) -> Dict[str, float]:
    home_strength = elo_expected_score(home_elo + 25, away_elo)
    return normalize({
        "home": (1 - draw_base) * home_strength,
        "draw": draw_base,
        "away": (1 - draw_base) * (1 - home_strength),
    })


def poisson_prob(lam: float, goals: int) -> float:
    return exp(-lam) * lam ** goals / factorial(goals)


def score_matrix(lambda_home: float, lambda_away: float, max_goals: int = 7) -> List[dict]:
    rows = []
    for home_goals in range(max_goals + 1):
        for away_goals in range(max_goals + 1):
            rows.append({
                "home_goals": home_goals,
                "away_goals": away_goals,
                "score": "{}:{}".format(home_goals, away_goals),
                "probability": poisson_prob(lambda_home, home_goals) * poisson_prob(lambda_away, away_goals),
            })
    total = sum(row["probability"] for row in rows)
    for row in rows:
        row["probability"] /= total
    return sorted(rows, key=lambda row: row["probability"], reverse=True)


def matrix_to_1x2(scores: List[dict]) -> Dict[str, float]:
    return normalize({
        "home": sum(row["probability"] for row in scores if row["home_goals"] > row["away_goals"]),
        "draw": sum(row["probability"] for row in scores if row["home_goals"] == row["away_goals"]),
        "away": sum(row["probability"] for row in scores if row["home_goals"] < row["away_goals"]),
    })


def totals_from_matrix(scores: List[dict]) -> Dict[str, float]:
    over = sum(row["probability"] for row in scores if row["home_goals"] + row["away_goals"] >= 3)
    btts = sum(row["probability"] for row in scores if row["home_goals"] and row["away_goals"])
    return {"over_25": over, "under_25": 1 - over, "btts": btts}


def remove_vig(odds: Dict[str, float]) -> Dict[str, float]:
    return normalize({key: 1 / value for key, value in odds.items() if value > 0})


def blend(model: Dict[str, float], market: Dict[str, float], market_weight: float) -> Dict[str, float]:
    return normalize({
        key: model[key] * (1 - market_weight) + market[key] * market_weight
        for key in ("home", "draw", "away")
    })


def brier_score(probs: Dict[str, float], actual: str) -> float:
    return sum((probs[key] - (1 if key == actual else 0)) ** 2 for key in ("home", "draw", "away"))


def log_loss(probs: Dict[str, float], actual: str) -> float:
    return -log(max(min(probs[actual], 1 - 1e-15), 1e-15))
