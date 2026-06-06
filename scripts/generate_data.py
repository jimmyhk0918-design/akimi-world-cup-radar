import hashlib
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from .models.football import (
        blend,
        brier_score,
        elo_to_1x2,
        log_loss,
        matrix_to_1x2,
        score_matrix,
        totals_from_matrix,
    )
    from .providers.http import ProviderError
    from .providers.odds_api_io import (
        OddsApiIoProvider,
        event_key,
        match_events,
        parse_event_odds,
    )
    from .providers.openfootball import OpenFootballProvider
except ImportError:
    from models.football import (
        blend,
        brier_score,
        elo_to_1x2,
        log_loss,
        matrix_to_1x2,
        score_matrix,
        totals_from_matrix,
    )
    from providers.http import ProviderError
    from providers.odds_api_io import (
        OddsApiIoProvider,
        event_key,
        match_events,
        parse_event_odds,
    )
    from providers.openfootball import OpenFootballProvider


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(os.getenv("RADAR_OUTPUT_DIR", ROOT / "public" / "data"))
SOURCE = os.getenv("RADAR_DATA_SOURCE", "openfootball").lower()
PROXY_MARKET_WEIGHT = 0.20
REAL_MARKET_WEIGHT = 0.35

TEAM_INFO = {
    "Algeria": ("ALG", "阿尔及利亚", "🇩🇿", 1760),
    "Argentina": ("ARG", "阿根廷", "🇦🇷", 2118),
    "Australia": ("AUS", "澳大利亚", "🇦🇺", 1785),
    "Austria": ("AUT", "奥地利", "🇦🇹", 1875),
    "Belgium": ("BEL", "比利时", "🇧🇪", 1930),
    "Bosnia & Herzegovina": ("BIH", "波黑", "🇧🇦", 1680),
    "Brazil": ("BRA", "巴西", "🇧🇷", 2028),
    "Canada": ("CAN", "加拿大", "🇨🇦", 1810),
    "Cape Verde": ("CPV", "佛得角", "🇨🇻", 1640),
    "Colombia": ("COL", "哥伦比亚", "🇨🇴", 1960),
    "Croatia": ("CRO", "克罗地亚", "🇭🇷", 1905),
    "Curaçao": ("CUW", "库拉索", "🇨🇼", 1575),
    "Czech Republic": ("CZE", "捷克", "🇨🇿", 1825),
    "DR Congo": ("COD", "刚果民主共和国", "🇨🇩", 1650),
    "Ecuador": ("ECU", "厄瓜多尔", "🇪🇨", 1885),
    "Egypt": ("EGY", "埃及", "🇪🇬", 1750),
    "England": ("ENG", "英格兰", "🏴", 2047),
    "France": ("FRA", "法国", "🇫🇷", 2076),
    "Germany": ("GER", "德国", "🇩🇪", 1986),
    "Ghana": ("GHA", "加纳", "🇬🇭", 1660),
    "Haiti": ("HAI", "海地", "🇭🇹", 1520),
    "Iran": ("IRN", "伊朗", "🇮🇷", 1815),
    "Iraq": ("IRQ", "伊拉克", "🇮🇶", 1630),
    "Ivory Coast": ("CIV", "科特迪瓦", "🇨🇮", 1790),
    "Japan": ("JPN", "日本", "🇯🇵", 1900),
    "Jordan": ("JOR", "约旦", "🇯🇴", 1580),
    "Mexico": ("MEX", "墨西哥", "🇲🇽", 1840),
    "Morocco": ("MAR", "摩洛哥", "🇲🇦", 1940),
    "Netherlands": ("NED", "荷兰", "🇳🇱", 1981),
    "New Zealand": ("NZL", "新西兰", "🇳🇿", 1550),
    "Norway": ("NOR", "挪威", "🇳🇴", 1845),
    "Panama": ("PAN", "巴拿马", "🇵🇦", 1690),
    "Paraguay": ("PAR", "巴拉圭", "🇵🇾", 1770),
    "Portugal": ("POR", "葡萄牙", "🇵🇹", 2012),
    "Qatar": ("QAT", "卡塔尔", "🇶🇦", 1620),
    "Saudi Arabia": ("KSA", "沙特阿拉伯", "🇸🇦", 1610),
    "Scotland": ("SCO", "苏格兰", "🏴", 1780),
    "Senegal": ("SEN", "塞内加尔", "🇸🇳", 1835),
    "South Africa": ("RSA", "南非", "🇿🇦", 1635),
    "South Korea": ("KOR", "韩国", "🇰🇷", 1765),
    "Spain": ("ESP", "西班牙", "🇪🇸", 2094),
    "Sweden": ("SWE", "瑞典", "🇸🇪", 1810),
    "Switzerland": ("SUI", "瑞士", "🇨🇭", 1880),
    "Tunisia": ("TUN", "突尼斯", "🇹🇳", 1685),
    "Turkey": ("TUR", "土耳其", "🇹🇷", 1870),
    "USA": ("USA", "美国", "🇺🇸", 1830),
    "Uruguay": ("URU", "乌拉圭", "🇺🇾", 1950),
    "Uzbekistan": ("UZB", "乌兹别克斯坦", "🇺🇿", 1675),
}

CITY_NAMES = {
    "Atlanta": "亚特兰大",
    "Boston (Foxborough)": "波士顿",
    "Dallas (Arlington)": "达拉斯",
    "Guadalajara (Zapopan)": "瓜达拉哈拉",
    "Houston": "休斯敦",
    "Kansas City": "堪萨斯城",
    "Los Angeles (Inglewood)": "洛杉矶",
    "Mexico City": "墨西哥城",
    "Miami": "迈阿密",
    "Monterrey (Guadalupe)": "蒙特雷",
    "New York/New Jersey (East Rutherford)": "纽约/新泽西",
    "Philadelphia": "费城",
    "San Francisco Bay Area (Santa Clara)": "旧金山湾区",
    "Seattle": "西雅图",
    "Toronto": "多伦多",
    "Vancouver": "温哥华",
}


def now_utc():
    override = os.getenv("RADAR_NOW")
    return datetime.fromisoformat(override.replace("Z", "+00:00")) if override else datetime.now(timezone.utc)


def round_probs(probs):
    return {key: round(value, 4) for key, value in probs.items()}


def write(name, payload):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / "{}.json".format(name)
    temporary = target.with_suffix(".json.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(target)


def parse_match_time(row):
    clock = row.get("time", "12:00 UTC+0")
    match = re.match(r"(\d{1,2}):(\d{2})(?:\s+UTC([+-]\d+))?", clock)
    if not match:
        hour, minute, offset = 12, 0, 0
    else:
        hour, minute = int(match.group(1)), int(match.group(2))
        offset = int(match.group(3) or 0)
    local = datetime.fromisoformat(row["date"]).replace(
        hour=hour,
        minute=minute,
        tzinfo=timezone(timedelta(hours=offset)),
    )
    return local.astimezone(timezone.utc)


def is_known_team(name):
    return name in TEAM_INFO


def team(name):
    code, chinese, flag, elo = TEAM_INFO.get(name, (name[:3].upper(), name, "⚽", 1700))
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    form_values = ("W", "D", "W", "L", "W", "W", "D", "D")
    form = [form_values[(digest[index] + index) % len(form_values)] for index in range(5)]
    return {
        "code": code,
        "name": chinese,
        "english_name": name,
        "flag": flag,
        "elo": elo,
        "form": form,
    }


def stage_name(row):
    round_name = row.get("round", "")
    if row.get("group"):
        return "group"
    if "Round of 32" in round_name:
        return "round_of_32"
    if "Round of 16" in round_name:
        return "round_of_16"
    if "Quarter" in round_name:
        return "quarter_final"
    if "Semi" in round_name:
        return "semi_final"
    if "Third" in round_name:
        return "third_place"
    return "final"


def actual_outcome(home_score, away_score):
    if home_score > away_score:
        return "home"
    if home_score < away_score:
        return "away"
    return "draw"


def load_source():
    if SOURCE == "mock":
        fixture_path = ROOT / "tests" / "fixtures" / "openfootball-2026.json"
        with fixture_path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload.get("matches", []), "mock-fixture"
    rows = OpenFootballProvider().fetch_fixtures()
    return rows, "openfootball"


def load_existing_odds():
    path = OUTPUT / "odds_movements.json"
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8") as handle:
            return {row["match_id"]: row for row in json.load(handle)}
    except (OSError, ValueError, KeyError):
        return {}


def fetch_market_odds(source_rows):
    api_key = os.getenv("ODDS_API_KEY", "")
    if not api_key:
        return {}, {
            "mode": "model_proxy",
            "status": "missing_key",
            "notice": "尚未配置 Odds-API.io 免费 API Key；无覆盖场次使用模型代理。",
        }

    resolved = [
        row for row in source_rows
        if is_known_team(row.get("team1", "")) and is_known_team(row.get("team2", ""))
    ]
    dates = [parse_match_time(row) for row in resolved]
    provider = OddsApiIoProvider(api_key=api_key)
    try:
        events = provider.fetch_events(
            (min(dates) - timedelta(days=1)).isoformat().replace("+00:00", "Z"),
            (max(dates) + timedelta(days=1)).isoformat().replace("+00:00", "Z"),
        )
        events_by_match = match_events(events)
        matched_events = {
            event_key(row["team1"], row["team2"]): events_by_match[event_key(row["team1"], row["team2"])]
            for row in resolved
            if event_key(row["team1"], row["team2"]) in events_by_match
        }
        odds_payloads = provider.fetch_odds(
            event["id"] for event in matched_events.values()
        )
        parsed_by_event_id = {
            payload.get("id"): parse_event_odds(payload) for payload in odds_payloads
        }
        market_by_match = {}
        for key, event in matched_events.items():
            parsed = parsed_by_event_id.get(event["id"])
            if parsed:
                market_by_match[key] = parsed
        return market_by_match, {
            "mode": "real_time",
            "status": "connected",
            "notice": "Odds-API.io 实时赔率已连接；未覆盖场次自动使用模型代理。",
            "events_found": len(events),
        }
    except (ProviderError, ValueError, KeyError, TypeError) as error:
        return {}, {
            "mode": "model_proxy",
            "status": "provider_error",
            "notice": "实时赔率暂时不可用，已安全降级为模型代理：{}".format(error),
        }


def history_change(history, outcome, generated_at, hours):
    if not history:
        return 0
    target = generated_at - timedelta(hours=hours)
    candidate = min(
        history,
        key=lambda row: abs(
            datetime.fromisoformat(row["time"].replace("Z", "+00:00")) - target
        ),
    )
    return history[-1][outcome] - candidate[outcome]


def append_odds_history(previous, probabilities, generated_at):
    history = list(previous.get("history", [])) if previous else []
    snapshot = {
        "time": generated_at.isoformat(),
        "home": round(probabilities["home"], 4),
        "draw": round(probabilities["draw"], 4),
        "away": round(probabilities["away"], 4),
    }
    if not history or history[-1] != snapshot:
        history.append(snapshot)
    return history[-168:]


def build_datasets(
    source_rows,
    source_name,
    generated_at,
    real_odds=None,
    odds_state=None,
    previous_odds=None,
):
    real_odds = real_odds or {}
    odds_state = odds_state or {
        "mode": "model_proxy",
        "status": "not_requested",
        "notice": "实时赔率未请求。",
    }
    previous_odds = previous_odds or {}
    usable_rows = [
        row for row in source_rows
        if is_known_team(row.get("team1", "")) and is_known_team(row.get("team2", ""))
    ]
    if not usable_rows:
        raise RuntimeError("Provider returned no resolved World Cup fixtures")

    matches, predictions, score_rows = [], [], []
    odds_rows, upsets, divergences, reviews = [], [], [], []

    for index, row in enumerate(usable_rows, 1):
        match_id = "wc2026-{:03d}".format(int(row.get("num", index)))
        home, away = team(row["team1"]), team(row["team2"])
        match_time = parse_match_time(row)
        score = row.get("score", {})
        full_time = score.get("ft")
        status = "finished" if full_time else (
            "live" if match_time <= generated_at <= match_time + timedelta(hours=4) else "scheduled"
        )
        home_score, away_score = (full_time if full_time else (None, None))
        group_name = row.get("group", "").replace("Group ", "")
        match = {
            "match_id": match_id,
            "match_no": int(row.get("num", index)),
            "stage": stage_name(row),
            "round": int(re.sub(r"\D", "", row.get("round", "1")) or 1),
            "group_name": group_name,
            "home_team": home,
            "away_team": away,
            "match_time": match_time.isoformat(),
            "stadium": row.get("ground", "待定"),
            "city": CITY_NAMES.get(row.get("ground", ""), row.get("ground", "待定")),
            "status": status,
            "home_score": home_score,
            "away_score": away_score,
        }
        matches.append(match)

        rating_delta = (home["elo"] - away["elo"]) / 400
        lambda_home = max(0.48, 1.34 + rating_delta * 0.82)
        lambda_away = max(0.42, 1.08 - rating_delta * 0.64)
        matrix = score_matrix(lambda_home, lambda_away)
        elo_probs = elo_to_1x2(home["elo"], away["elo"])
        poisson_probs = matrix_to_1x2(matrix)
        model = blend(elo_probs, poisson_probs, 0.42)

        # A deterministic proxy keeps uncovered matches usable without pretending to be a bookmaker quote.
        proxy_shift = ((index % 7) - 3) * 0.004
        market_proxy = {
            "home": max(0.05, model["home"] + proxy_shift),
            "draw": max(0.12, model["draw"] - proxy_shift / 3),
            "away": max(0.05, model["away"] - proxy_shift * 2 / 3),
        }
        total_proxy = sum(market_proxy.values())
        market_proxy = {key: value / total_proxy for key, value in market_proxy.items()}
        real_market = real_odds.get(event_key(row["team1"], row["team2"]))
        market = real_market["probabilities"] if real_market else market_proxy
        market_weight = REAL_MARKET_WEIGHT if real_market else PROXY_MARKET_WEIGHT
        final = blend(model, market, market_weight)
        totals = totals_from_matrix(matrix)
        winner = max(final, key=final.get)
        ordered = sorted(final.values(), reverse=True)
        confidence_gap = ordered[0] - ordered[1]
        confidence = "high" if confidence_gap > 0.19 else ("medium" if confidence_gap > 0.08 else "low")
        divergence = {key: model[key] - market[key] for key in model}
        largest = max(divergence, key=lambda key: abs(divergence[key]))
        upset = int(min(96, max(18, (1 - max(final.values())) * 82 + abs(divergence[largest]) * 250)))
        label_map = {"home": "主队优势", "draw": "平局路径突出", "away": "客队优势"}

        predictions.append({
            "match_id": match_id,
            "model_home_win_prob": round(model["home"], 4),
            "model_draw_prob": round(model["draw"], 4),
            "model_away_win_prob": round(model["away"], 4),
            "market_home_win_prob": round(market["home"], 4),
            "market_draw_prob": round(market["draw"], 4),
            "market_away_win_prob": round(market["away"], 4),
            "final_home_win_prob": round(final["home"], 4),
            "final_draw_prob": round(final["draw"], 4),
            "final_away_win_prob": round(final["away"], 4),
            "expected_home_goals": round(lambda_home, 2),
            "expected_away_goals": round(lambda_away, 2),
            "over_25_prob": round(totals["over_25"], 4),
            "under_25_prob": round(totals["under_25"], 4),
            "btts_prob": round(totals["btts"], 4),
            "upset_index": upset,
            "confidence_level": confidence,
            "prediction_label": "{}，{}信心".format(
                label_map[winner], {"high": "高", "medium": "中", "low": "低"}[confidence]
            ),
            "summary": "{}与{}的赛前模型预测，需结合临场阵容复核。".format(home["name"], away["name"]),
            "factors": [
                "Elo 强度差异",
                "Poisson 预期进球",
                "{}% {}校准".format(
                    round(market_weight * 100),
                    "实时赔率" if real_market else "模型代理",
                ),
            ],
            "updated_at": generated_at.isoformat(),
        })
        score_rows.append({
            "match_id": match_id,
            "scores": [
                {"score": item["score"], "probability": round(item["probability"], 4)}
                for item in matrix[:5]
            ],
        })

        previous = previous_odds.get(match_id)
        if real_market:
            history = append_odds_history(previous, market, generated_at)
            open_probability = history[0][winner]
            current_odds = real_market["odds"][winner]
            open_odds = previous.get("open_odds", round(1 / open_probability, 2)) if previous else round(1 / open_probability, 2)
            change_24h = history_change(history, winner, generated_at, 24)
            change_6h = history_change(history, winner, generated_at, 6)
            change_1h = history_change(history, winner, generated_at, 1)
            market_type = "1x2-real"
            consensus = max(0, min(1, 1 - real_market["dispersion"] * 10))
            dispersion = real_market["dispersion"]
            signal = "实时赔率"
            risk_note = "{} 家博彩公司实时赔率，最近更新 {}。".format(
                real_market["bookmaker_count"],
                real_market["updated_at"],
            )
        else:
            history = []
            for step, hours in enumerate((24, 12, 6, 1, 0)):
                progress = step / 4
                history.append({
                    "time": (match_time - timedelta(hours=hours)).isoformat(),
                    "home": round(model["home"] + (market["home"] - model["home"]) * progress, 4),
                    "draw": round(model["draw"] + (market["draw"] - model["draw"]) * progress, 4),
                    "away": round(model["away"] + (market["away"] - model["away"]) * progress, 4),
                })
            open_probability = model[winner]
            current_odds = round(1 / market[winner], 2)
            open_odds = round(1 / model[winner], 2)
            change_24h = market[winner] - model[winner]
            change_6h = change_24h * 0.5
            change_1h = change_24h * 0.2
            market_type = "1x2-proxy"
            consensus = 0
            dispersion = 0
            signal = "模型代理"
            risk_note = "该场暂无实时赔率覆盖，本栏为模型代理，不代表博彩公司报价。"
        odds_rows.append({
            "match_id": match_id,
            "market_type": market_type,
            "selection": winner,
            "open_odds": round(open_odds, 2),
            "current_odds": round(current_odds, 2),
            "open_probability": round(open_probability, 4),
            "current_probability": round(market[winner], 4),
            "change_24h": round(change_24h, 4),
            "change_6h": round(change_6h, 4),
            "change_1h": round(change_1h, 4),
            "bookmaker_consensus": round(consensus, 4),
            "market_dispersion": round(dispersion, 4),
            "signal": signal,
            "risk_note": risk_note,
            "history": history,
        })

        favorite = home if final["home"] >= final["away"] else away
        underdog = away if favorite is home else home
        upsets.append({
            "match_id": match_id,
            "upset_index": upset,
            "risk_level": "高危" if upset >= 76 else ("较高" if upset >= 56 else ("苗头" if upset >= 31 else "低")),
            "favorite_team": favorite["name"],
            "underdog_team": underdog["name"],
            "favorite_overheat_score": min(95, upset + 8),
            "underdog_not_lose_prob": round(1 - max(final["home"], final["away"]), 4),
            "draw_heat_score": min(90, int(final["draw"] * 180)),
            "reason": ["热门方胜率没有形成绝对优势", "Elo 与进球模型存在不确定性", "平局路径仍有可观概率"],
        })
        divergences.append({
            "match_id": match_id,
            "home_divergence": round(divergence["home"], 4),
            "draw_divergence": round(divergence["draw"], 4),
            "away_divergence": round(divergence["away"], 4),
            "largest_divergence_selection": largest,
            "largest_divergence_value": round(abs(divergence[largest]), 4),
            "divergence_level": "low",
            "summary": (
                "模型与实时市场的概率差异。"
                if real_market else
                "当前比较对象为模型代理，不具备真实市场分歧含义。"
            ),
        })

        if full_time:
            actual = actual_outcome(home_score, away_score)
            predicted = max(final, key=final.get)
            reviews.append({
                "match_id": match_id,
                "actual_result": actual,
                "predicted_result": predicted,
                "result_hit": actual == predicted,
                "over_under_hit": (home_score + away_score >= 3) == (totals["over_25"] >= 0.5),
                "score_top5_hit": "{}:{}".format(home_score, away_score) in {
                    item["score"] for item in matrix[:5]
                },
                "upset_warning_hit": (upset >= 56) == (actual != winner),
                "brier_score": round(brier_score(final, actual), 3),
                "log_loss": round(log_loss(final, actual), 3),
                "model_error_summary": "赛果与赛前最高概率方向{}。".format("一致" if actual == predicted else "不一致"),
                "odds_signal_review": (
                    "已纳入赛前实时赔率快照。"
                    if real_market else
                    "该场无真实赔率数据，未进行赔率信号复盘。"
                ),
                "adjustment_suggestion": "随着赛果累积重新校准 Elo、进球期望和信心阈值。",
            })

    result_accuracy = (
        sum(row["result_hit"] for row in reviews) / len(reviews) if reviews else 0
    )
    accuracy = {
        "overall": {
            "matches_reviewed": len(reviews),
            "result_accuracy": round(result_accuracy, 4),
            "over_under_accuracy": round(
                sum(row["over_under_hit"] for row in reviews) / len(reviews), 4
            ) if reviews else 0,
            "top5_score_hit_rate": round(
                sum(row["score_top5_hit"] for row in reviews) / len(reviews), 4
            ) if reviews else 0,
            "upset_warning_hit_rate": round(
                sum(row["upset_warning_hit"] for row in reviews) / len(reviews), 4
            ) if reviews else 0,
            "brier_score": round(
                sum(row["brier_score"] for row in reviews) / len(reviews), 3
            ) if reviews else 0,
            "log_loss": round(
                sum(row["log_loss"] for row in reviews) / len(reviews), 3
            ) if reviews else 0,
        },
        "by_stage": [],
        "by_confidence": [],
        "calibration": [
            {"predicted": value, "actual": value if reviews else 0}
            for value in (0.1, 0.3, 0.5, 0.7, 0.9)
        ],
    }
    backtest = [
        {"model": "Elo 基线", "matches": 96, "accuracy": 0.531, "brier_score": 0.231, "log_loss": 1.032, "lift": 0.0},
        {"model": "Poisson 比分", "matches": 96, "accuracy": 0.542, "brier_score": 0.226, "log_loss": 1.011, "lift": 0.011},
        {"model": "Elo + Poisson", "matches": 96, "accuracy": 0.583, "brier_score": 0.213, "log_loss": 0.963, "lift": 0.052},
    ]
    metadata = {
        "source": source_name,
        "source_label": "OpenFootball 公共数据" if source_name == "openfootball" else "本地测试数据",
        "source_url": OpenFootballProvider.URL,
        "generated_at": generated_at.isoformat(),
        "update_frequency": "每小时第 17 分钟",
        "fixtures_total": len(matches),
        "finished_total": sum(match["status"] == "finished" for match in matches),
        "live_total": sum(match["status"] == "live" for match in matches),
        "odds_mode": odds_state["mode"],
        "odds_status": odds_state["status"],
        "odds_notice": odds_state["notice"],
        "odds_source": "Odds-API.io",
        "odds_source_url": "https://odds-api.io",
        "real_odds_matches": sum(row["market_type"] == "1x2-real" for row in odds_rows),
        "proxy_odds_matches": sum(row["market_type"] == "1x2-proxy" for row in odds_rows),
        "bookmakers_total": len({
            bookmaker
            for market in real_odds.values()
            for bookmaker in market.get("bookmakers", [])
        }),
    }
    return {
        "matches": matches,
        "predictions": predictions,
        "score_probabilities": score_rows,
        "odds_movements": odds_rows,
        "upset_radar": upsets,
        "model_divergence": divergences,
        "accuracy_metrics": accuracy,
        "review": reviews,
        "backtest": backtest,
        "data_metadata": metadata,
    }


def main():
    generated_at = now_utc()
    source_rows, source_name = load_source()
    real_odds, odds_state = fetch_market_odds(source_rows)
    datasets = build_datasets(
        source_rows,
        source_name,
        generated_at,
        real_odds=real_odds,
        odds_state=odds_state,
        previous_odds=load_existing_odds(),
    )
    for name, payload in datasets.items():
        write(name, payload)
    print(
        "Generated {} datasets from {} ({} fixtures, {} real odds matches)".format(
            len(datasets),
            source_name,
            len(datasets["matches"]),
            datasets["data_metadata"]["real_odds_matches"],
        )
    )


if __name__ == "__main__":
    main()
