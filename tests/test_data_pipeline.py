import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.generate_data import build_datasets, parse_match_time


ROOT = Path(__file__).resolve().parents[1]


class DataPipelineTests(unittest.TestCase):
    def test_parses_openfootball_utc_offset(self):
        parsed = parse_match_time({
            "date": "2026-06-11",
            "time": "13:00 UTC-6",
        })
        self.assertEqual(parsed.isoformat(), "2026-06-11T19:00:00+00:00")

    def test_builds_only_resolved_fixtures_and_reviews_scores(self):
        with (ROOT / "tests" / "fixtures" / "openfootball-2026.json").open() as handle:
            rows = json.load(handle)["matches"]
        generated_at = parse_match_time({"date": "2026-06-12", "time": "12:00 UTC+0"})
        data = build_datasets(rows, "mock-fixture", generated_at)
        self.assertEqual(len(data["matches"]), 2)
        self.assertEqual(len(data["review"]), 1)
        self.assertEqual(data["data_metadata"]["fixtures_total"], 2)
        self.assertEqual(data["odds_movements"][0]["market_type"], "1x2-proxy")

    def test_mock_cli_path_does_not_need_network(self):
        env = os.environ.copy()
        env["RADAR_DATA_SOURCE"] = "mock"
        env["RADAR_NOW"] = "2026-06-07T00:00:00Z"
        with tempfile.TemporaryDirectory() as output:
            env["RADAR_OUTPUT_DIR"] = output
            result = subprocess.run(
                ["python3", "scripts/generate_data.py"],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("mock-fixture", result.stdout)


if __name__ == "__main__":
    unittest.main()
