import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from models.football import blend, elo_to_1x2, matrix_to_1x2, remove_vig, score_matrix, totals_from_matrix


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "public" / "data"
NOW = datetime(2026, 6, 6, 6, 0, tzinfo=timezone.utc)
random.seed(2026)

TEAMS = {
    "ARG": ("阿根廷", "Argentina", "🇦🇷", 2118),
    "ESP": ("西班牙", "Spain", "🇪🇸", 2094),
    "FRA": ("法国", "France", "🇫🇷", 2076),
    "ENG": ("英格兰", "England", "🏴", 2047),
    "BRA": ("巴西", "Brazil", "🇧🇷", 2028),
    "POR": ("葡萄牙", "Portugal", "🇵🇹", 2012),
    "GER": ("德国", "Germany", "🇩🇪", 1986),
    "NED": ("荷兰", "Netherlands", "🇳🇱", 1981),
}

FIXTURES = [
    ("m001", "ARG", "ESP", "A", 6, "纽约新泽西体育场", "纽约"),
    ("m002", "FRA", "ENG", "A", 9, "洛杉矶体育场", "洛杉矶"),
    ("m003", "BRA", "POR", "B", 13, "迈阿密体育场", "迈阿密"),
    ("m004", "GER", "NED", "B", 16, "多伦多体育场", "多伦多"),
    ("m005", "ARG", "FRA", "A", 20, "达拉斯体育场", "达拉斯"),
    ("m006", "ESP", "ENG", "A", 23, "亚特兰大体育场", "亚特兰大"),
    ("m007", "BRA", "GER", "B", 27, "休斯敦体育场", "休斯敦"),
    ("m008", "POR", "NED", "B", 30, "波士顿体育场", "波士顿"),
    ("m009", "ARG", "ENG", "A", 34, "费城体育场", "费城"),
    ("m010", "ESP", "FRA", "A", 37, "西雅图体育场", "西雅图"),
    ("m011", "BRA", "NED", "B", 41, "旧金山湾区体育场", "旧金山"),
    ("m012", "POR", "GER", "B", 44, "温哥华体育场", "温哥华"),
]


def team(code):
    name, english, flag, elo = TEAMS[code]
    forms = [["W", "W", "D", "W", "L"], ["W", "D", "W", "W", "W"], ["D", "W", "W", "L", "W"]]
    return {"code": code, "name": name, "english_name": english, "flag": flag, "elo": elo, "form": forms[sum(map(ord, code)) % 3]}


def round_probs(probs):
    return {key: round(value, 4) for key, value in probs.items()}


def write(name, payload):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "{}.json".format(name)).open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def main():
    matches, predictions, score_rows, odds_rows, upsets, divergences = [], [], [], [], [], []
    for index, (match_id, home_code, away_code, group, hour_offset, stadium, city) in enumerate(FIXTURES, 1):
        home, away = team(home_code), team(away_code)
        match_time = NOW + timedelta(days=5 + index // 4, hours=hour_offset)
        status = "finished" if index <= 4 else ("live" if index == 5 else "scheduled")
        match = {
            "match_id": match_id, "match_no": index, "stage": "group", "round": (index - 1) // 4 + 1,
            "group_name": group, "home_team": home, "away_team": away, "match_time": match_time.isoformat(),
            "stadium": stadium, "city": city, "status": status,
            "home_score": [2, 1, 0, 2, 1][index - 1] if index <= 5 else None,
            "away_score": [1, 1, 1, 2, 1][index - 1] if index <= 5 else None,
        }
        if status == "live":
            match["minute"] = 63
        matches.append(match)

        rating_delta = (home["elo"] - away["elo"]) / 400
        lambda_home = max(0.55, 1.35 + rating_delta * 0.85 + (index % 3 - 1) * 0.12)
        lambda_away = max(0.48, 1.08 - rating_delta * 0.65 + ((index + 1) % 3 - 1) * 0.1)
        matrix = score_matrix(lambda_home, lambda_away)
        elo_probs = elo_to_1x2(home["elo"], away["elo"])
        poisson_probs = matrix_to_1x2(matrix)
        model = blend(elo_probs, poisson_probs, 0.42)

        market_shift = ((index % 5) - 2) * 0.009
        market_seed = {
            "home": max(0.08, model["home"] + market_shift),
            "draw": max(0.12, model["draw"] - market_shift / 3),
            "away": max(0.08, model["away"] - market_shift * 2 / 3),
        }
        market_odds = {key: 1 / value * 1.06 for key, value in market_seed.items()}
        market = remove_vig(market_odds)
        final = blend(model, market, 0.35)
        totals = totals_from_matrix(matrix)
        winner = max(final, key=final.get)
        confidence_gap = sorted(final.values(), reverse=True)[0] - sorted(final.values(), reverse=True)[1]
        confidence = "high" if confidence_gap > 0.19 else ("medium" if confidence_gap > 0.08 else "low")
        divergence = {key: model[key] - market[key] for key in model}
        largest = max(divergence, key=lambda key: abs(divergence[key]))
        upset = int(min(96, max(18, (1 - max(final.values())) * 78 + abs(divergence["home"]) * 310 + (index % 4) * 5)))
        label_map = {"home": "主队优势", "draw": "平局路径突出", "away": "客队优势"}

        predictions.append({
            "match_id": match_id,
            **{"model_{}_win_prob".format(key) if key != "draw" else "model_draw_prob": value for key, value in round_probs(model).items()},
            **{"market_{}_win_prob".format(key) if key != "draw" else "market_draw_prob": value for key, value in round_probs(market).items()},
            **{"final_{}_win_prob".format(key) if key != "draw" else "final_draw_prob": value for key, value in round_probs(final).items()},
            "expected_home_goals": round(lambda_home, 2), "expected_away_goals": round(lambda_away, 2),
            "over_25_prob": round(totals["over_25"], 4), "under_25_prob": round(totals["under_25"], 4),
            "btts_prob": round(totals["btts"], 4), "upset_index": upset, "confidence_level": confidence,
            "prediction_label": "{}，{}信心".format(label_map[winner], {"high": "高", "medium": "中", "low": "低"}[confidence]),
            "summary": "{}略占优势，但模型保留{}与小比分路径。".format(home["name"] if winner == "home" else away["name"], "平局" if winner != "draw" else "双方"),
            "factors": ["Elo 强度差异已纳入", "Poisson 预期进球完成校准", "市场概率权重为 35%"],
            "updated_at": NOW.isoformat(),
        })
        score_rows.append({"match_id": match_id, "scores": [{"score": row["score"], "probability": round(row["probability"], 4)} for row in matrix[:5]]})

        history = []
        for step, hours in enumerate((24, 12, 6, 1, 0)):
            progress = step / 4
            history.append({
                "time": (match_time - timedelta(hours=hours)).isoformat(),
                "home": round(model["home"] + (market["home"] - model["home"]) * progress, 4),
                "draw": round(model["draw"] + (market["draw"] - model["draw"]) * progress, 4),
                "away": round(model["away"] + (market["away"] - model["away"]) * progress, 4),
            })
        open_odds = 1 / max(0.08, model[winner]) * 1.06
        current_odds = market_odds[winner]
        odds_rows.append({
            "match_id": match_id, "market_type": "1x2", "selection": winner,
            "open_odds": round(open_odds, 2), "current_odds": round(current_odds, 2),
            "open_probability": round(model[winner], 4), "current_probability": round(market[winner], 4),
            "change_24h": round(market[winner] - model[winner], 4),
            "change_6h": round((market[winner] - model[winner]) * 0.5, 4),
            "change_1h": round((market[winner] - model[winner]) * 0.2, 4),
            "bookmaker_consensus": round(0.62 + (index % 4) * 0.08, 2),
            "market_dispersion": round(0.025 + (index % 3) * 0.018, 3),
            "signal": {"home": "主队升温", "draw": "平局升温", "away": "客队升温"}[winner],
            "risk_note": "市场与模型存在{}分歧，需结合临场阵容复核。".format("明显" if abs(divergence[winner]) > 0.05 else "轻微"),
            "history": history,
        })
        favorite = home if final["home"] >= final["away"] else away
        underdog = away if favorite is home else home
        upsets.append({
            "match_id": match_id, "upset_index": upset,
            "risk_level": "高危" if upset >= 76 else ("较高" if upset >= 56 else ("苗头" if upset >= 31 else "低")),
            "favorite_team": favorite["name"], "underdog_team": underdog["name"],
            "favorite_overheat_score": min(95, upset + 8), "underdog_not_lose_prob": round(1 - max(final["home"], final["away"]), 4),
            "draw_heat_score": min(90, int(final["draw"] * 180)),
            "reason": ["热门方胜率没有形成绝对优势", "市场热度与模型支持力度存在偏差", "平局路径仍有可观概率"],
        })
        divergences.append({
            "match_id": match_id, "home_divergence": round(divergence["home"], 4),
            "draw_divergence": round(divergence["draw"], 4), "away_divergence": round(divergence["away"], 4),
            "largest_divergence_selection": largest, "largest_divergence_value": round(abs(divergence[largest]), 4),
            "divergence_level": "high" if abs(divergence[largest]) >= 0.12 else ("medium" if abs(divergence[largest]) >= 0.03 else "low"),
            "summary": "市场比模型更{}，当前属于{}分歧。".format("看好热门方向" if divergence[largest] < 0 else "谨慎", "明显" if abs(divergence[largest]) >= 0.07 else "轻微"),
        })

    reviews = [
        {
            "match_id": match["match_id"], "actual_result": ["home", "draw", "away", "draw"][i],
            "predicted_result": max(
                {"home": predictions[i]["final_home_win_prob"], "draw": predictions[i]["final_draw_prob"], "away": predictions[i]["final_away_win_prob"]},
                key=lambda key: {"home": predictions[i]["final_home_win_prob"], "draw": predictions[i]["final_draw_prob"], "away": predictions[i]["final_away_win_prob"]}[key],
            ),
            "result_hit": i in (0, 2), "over_under_hit": i != 1, "score_top5_hit": i in (0, 3),
            "upset_warning_hit": i in (1, 3), "brier_score": round(0.18 + i * 0.073, 3),
            "log_loss": round(0.62 + i * 0.19, 3),
            "model_error_summary": ["判断基本准确，主队优势兑现。", "低估了平局韧性。", "客队防守转换效率高于预期。", "双方实力接近，模型方向不够明确。"][i],
            "odds_signal_review": "赔率变化提供了风险提示，但不应单独作为方向判断。",
            "adjustment_suggestion": "同类高分歧场次降低信心等级，并提高平局先验。",
        } for i, match in enumerate(matches[:4])
    ]
    accuracy = {
        "overall": {"matches_reviewed": 48, "result_accuracy": 0.604, "over_under_accuracy": 0.625, "top5_score_hit_rate": 0.292, "upset_warning_hit_rate": 0.458, "brier_score": 0.207, "log_loss": 0.941},
        "by_stage": [
            {"stage": "小组赛第一轮", "matches": 16, "result_accuracy": 0.562, "brier_score": 0.221},
            {"stage": "小组赛第二轮", "matches": 16, "result_accuracy": 0.625, "brier_score": 0.201},
            {"stage": "小组赛第三轮", "matches": 16, "result_accuracy": 0.625, "brier_score": 0.199},
        ],
        "by_confidence": [
            {"confidence_level": "high", "matches": 12, "result_accuracy": 0.75},
            {"confidence_level": "medium", "matches": 24, "result_accuracy": 0.625},
            {"confidence_level": "low", "matches": 12, "result_accuracy": 0.417},
        ],
        "calibration": [{"predicted": p, "actual": max(0.02, min(0.98, p + shift))} for p, shift in ((0.1, 0.02), (0.3, -0.03), (0.5, 0.01), (0.7, -0.04), (0.9, -0.08))],
    }
    backtest = [
        {"model": "Elo 基线", "matches": 96, "accuracy": 0.531, "brier_score": 0.231, "log_loss": 1.032, "lift": 0.0},
        {"model": "Poisson 比分", "matches": 96, "accuracy": 0.542, "brier_score": 0.226, "log_loss": 1.011, "lift": 0.011},
        {"model": "市场去水概率", "matches": 96, "accuracy": 0.573, "brier_score": 0.216, "log_loss": 0.976, "lift": 0.042},
        {"model": "Elo + Poisson", "matches": 96, "accuracy": 0.583, "brier_score": 0.213, "log_loss": 0.963, "lift": 0.052},
        {"model": "模型 + 市场校准", "matches": 96, "accuracy": 0.604, "brier_score": 0.207, "log_loss": 0.941, "lift": 0.073},
        {"model": "临场阶段修正", "matches": 96, "accuracy": 0.615, "brier_score": 0.203, "log_loss": 0.928, "lift": 0.084},
    ]
    for name, payload in {
        "matches": matches, "predictions": predictions, "score_probabilities": score_rows,
        "odds_movements": odds_rows, "upset_radar": upsets, "model_divergence": divergences,
        "accuracy_metrics": accuracy, "review": reviews, "backtest": backtest,
    }.items():
        write(name, payload)
    print("Generated {} datasets in {}".format(9, OUTPUT))


if __name__ == "__main__":
    main()
