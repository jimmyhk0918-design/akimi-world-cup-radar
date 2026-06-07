import unittest

from scripts.models.context import (
    adjust_expected_goals,
    default_intelligence,
    merge_intelligence,
    score_intelligence,
)


class ContextModelTests(unittest.TestCase):
    def test_missing_features_are_neutral(self):
        intelligence = score_intelligence(default_intelligence("m1"))
        home, away = adjust_expected_goals(1.4, 1.1, intelligence)
        self.assertEqual(home, 1.4)
        self.assertEqual(away, 1.1)
        self.assertEqual(intelligence["completeness"], 0)

    def test_confirmed_features_adjust_expected_goals(self):
        intelligence = merge_intelligence(default_intelligence("m1"), {
            "features": {
                "recent_form": {
                    "status": "verified",
                    "home_impact": 0.7,
                    "away_impact": -0.2,
                    "summary": "主队最近10场表现更稳定。",
                    "source_url": "https://example.com/results",
                },
                "availability": {
                    "status": "confirmed",
                    "home_impact": 0.2,
                    "away_impact": -0.8,
                    "summary": "客队核心前锋官方确认缺席。",
                    "source_url": "https://example.com/official-squad",
                },
            },
        })
        intelligence = score_intelligence(intelligence)
        home, away = adjust_expected_goals(1.4, 1.1, intelligence)
        self.assertGreater(home, 1.4)
        self.assertLess(away, 1.1)
        self.assertAlmostEqual(intelligence["completeness"], 0.4)

    def test_confirmed_lineup_requires_source(self):
        intelligence = merge_intelligence(default_intelligence("m1"), {
            "features": {
                "lineup": {
                    "status": "confirmed",
                    "summary": "首发已公布。",
                },
            },
        })
        with self.assertRaises(ValueError):
            score_intelligence(intelligence)


if __name__ == "__main__":
    unittest.main()
