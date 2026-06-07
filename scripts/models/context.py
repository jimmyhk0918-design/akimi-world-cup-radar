from copy import deepcopy
from typing import Dict, Iterable, Tuple


FEATURE_WEIGHTS = {
    "recent_form": 0.20,
    "availability": 0.20,
    "lineup": 0.15,
    "fatigue": 0.10,
    "motivation": 0.10,
    "tactical": 0.10,
    "weather": 0.05,
    "market": 0.10,
}

TRUSTED_STATUSES = {"confirmed", "automatic", "verified"}


def feature_template(label: str, status: str = "missing") -> Dict:
    return {
        "label": label,
        "status": status,
        "home_impact": 0.0,
        "away_impact": 0.0,
        "summary": "暂无可靠数据，保持中性。",
        "source_name": "",
        "source_url": "",
        "published_at": "",
        "updated_at": "",
        "details": [],
    }


def default_intelligence(match_id: str, market_is_real: bool = False) -> Dict:
    features = {
        "recent_form": feature_template("最近10场状态"),
        "availability": feature_template("伤病与停赛", "pending_official"),
        "lineup": feature_template("预计与确认首发", "pending_official"),
        "fatigue": feature_template("赛程疲劳"),
        "motivation": feature_template("比赛动机"),
        "tactical": feature_template("战术克制"),
        "weather": feature_template("天气与场地", "forecast_pending"),
        "market": feature_template(
            "临场赔率", "automatic" if market_is_real else "proxy"
        ),
    }
    features["market"]["summary"] = (
        "已接入多家公司实时赔率。"
        if market_is_real else
        "暂无真实赔率覆盖，使用模型代理且不计入情报完整度。"
    )
    return {
        "match_id": match_id,
        "features": features,
        "completeness": 0.0,
        "confirmed_features": 0,
        "total_features": len(FEATURE_WEIGHTS),
        "home_context_adjustment": 0.0,
        "away_context_adjustment": 0.0,
        "warning": "动态情报尚不完整，概率主要由基础实力与进球模型驱动。",
    }


def merge_intelligence(base: Dict, override: Dict) -> Dict:
    merged = deepcopy(base)
    for feature_name, values in override.get("features", {}).items():
        if feature_name not in merged["features"] or not isinstance(values, dict):
            continue
        merged["features"][feature_name].update(values)
    return merged


def validate_official_sources(intelligence: Dict) -> None:
    for name in ("availability", "lineup"):
        feature = intelligence["features"][name]
        if feature.get("status") == "confirmed" and not feature.get("source_url"):
            raise ValueError("{} confirmed data requires source_url".format(name))


def _trusted_features(features: Dict) -> Iterable[Tuple[str, Dict]]:
    return (
        (name, feature)
        for name, feature in features.items()
        if feature.get("status") in TRUSTED_STATUSES
    )


def score_intelligence(intelligence: Dict) -> Dict:
    validate_official_sources(intelligence)
    features = intelligence["features"]
    trusted = list(_trusted_features(features))
    completeness = sum(FEATURE_WEIGHTS[name] for name, _ in trusted)
    home_adjustment = sum(
        FEATURE_WEIGHTS[name] * max(-1.0, min(1.0, float(feature.get("home_impact", 0))))
        for name, feature in trusted
    )
    away_adjustment = sum(
        FEATURE_WEIGHTS[name] * max(-1.0, min(1.0, float(feature.get("away_impact", 0))))
        for name, feature in trusted
    )
    intelligence["completeness"] = round(completeness, 4)
    intelligence["confirmed_features"] = len(trusted)
    intelligence["home_context_adjustment"] = round(home_adjustment, 4)
    intelligence["away_context_adjustment"] = round(away_adjustment, 4)
    intelligence["warning"] = (
        "动态情报覆盖充分。"
        if completeness >= 0.75 else
        "动态情报覆盖有限，缺失项保持中性且不会被模型臆测。"
    )
    return intelligence


def adjust_expected_goals(
    lambda_home: float,
    lambda_away: float,
    intelligence: Dict,
) -> Tuple[float, float]:
    home = intelligence["home_context_adjustment"]
    away = intelligence["away_context_adjustment"]
    adjusted_home = lambda_home * (1 + home * 0.35 - away * 0.12)
    adjusted_away = lambda_away * (1 + away * 0.35 - home * 0.12)
    return max(0.25, adjusted_home), max(0.25, adjusted_away)
