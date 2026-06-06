import math
import unittest

from scripts.models.football import (
    blend,
    brier_score,
    elo_expected_score,
    elo_to_1x2,
    log_loss,
    matrix_to_1x2,
    remove_vig,
    score_matrix,
    totals_from_matrix,
)


class FootballModelTests(unittest.TestCase):
    def assert_probability_distribution(self, values):
        self.assertAlmostEqual(sum(values.values()), 1.0, places=8)
        self.assertTrue(all(0 <= value <= 1 for value in values.values()))

    def test_equal_elo_is_near_balanced_with_home_advantage(self):
        probs = elo_to_1x2(1900, 1900)
        self.assert_probability_distribution(probs)
        self.assertGreater(probs["home"], probs["away"])
        self.assertAlmostEqual(probs["draw"], 0.26, places=5)

    def test_score_matrix_normalizes_truncated_tail(self):
        scores = score_matrix(1.55, 0.92)
        self.assertAlmostEqual(sum(row["probability"] for row in scores), 1.0, places=8)
        self.assertEqual(scores, sorted(scores, key=lambda row: row["probability"], reverse=True))

    def test_matrix_outputs_valid_markets(self):
        scores = score_matrix(1.4, 1.1)
        self.assert_probability_distribution(matrix_to_1x2(scores))
        totals = totals_from_matrix(scores)
        self.assertAlmostEqual(totals["over_25"] + totals["under_25"], 1.0, places=8)
        self.assertTrue(0 <= totals["btts"] <= 1)

    def test_remove_vig(self):
        probs = remove_vig({"home": 1.8, "draw": 3.5, "away": 4.8})
        self.assert_probability_distribution(probs)
        self.assertGreater(probs["home"], probs["draw"])

    def test_blend_boundaries(self):
        model = {"home": 0.5, "draw": 0.3, "away": 0.2}
        market = {"home": 0.4, "draw": 0.3, "away": 0.3}
        self.assertEqual(blend(model, market, 0), model)
        self.assertEqual(blend(model, market, 1), market)

    def test_scoring_rules_reward_correct_confidence(self):
        good = {"home": 0.7, "draw": 0.2, "away": 0.1}
        poor = {"home": 0.2, "draw": 0.3, "away": 0.5}
        self.assertLess(brier_score(good, "home"), brier_score(poor, "home"))
        self.assertLess(log_loss(good, "home"), log_loss(poor, "home"))
        self.assertTrue(math.isfinite(log_loss({"home": 0, "draw": 0.5, "away": 0.5}, "home")))

    def test_elo_expected_score_monotonic(self):
        self.assertGreater(elo_expected_score(2100, 1900), elo_expected_score(2000, 1900))


if __name__ == "__main__":
    unittest.main()
