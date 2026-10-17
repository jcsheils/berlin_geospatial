import csv
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from berlin_heat.watering_temporal import (
    ACTIVE_SEASON_MONTHS,
    REFERENCE_YEARS,
    _validate_panel,
    _write_year_atlas,
    build_watering_temporal_atlas,
    classify_map_value,
    derive_shared_positive_breaks,
    season_for_month,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPORAL = ROOT / "data/processed/temporal"
CALENDAR_LOR = TEMPORAL / "lor_calendar_month_recorded_watering_2021_2025.csv"
CITY_MONTH = TEMPORAL / "berlin_month_recorded_watering_2020_2025.csv"
CITY_CALENDAR = TEMPORAL / "berlin_calendar_month_recorded_watering_2021_2025.csv"
SEASON = TEMPORAL / "berlin_season_recorded_watering_2021_2025.csv"
YEAR_SUMMARY = TEMPORAL / "berlin_year_recorded_watering_2021_2025.csv"
METADATA = TEMPORAL / "watering_temporal_atlas_2020_2025.metadata.json"
REPORT = ROOT / "output/03_spatial_equity_vulnerability"
TIMING_FIGURE = REPORT / "figures/01_recorded_watering_monthly_timing.png"
CALENDAR_ATLAS = REPORT / "maps/01_calendar_month_recorded_watering_atlas.png"
ACTIVE_ATLAS = REPORT / "maps/02_active_season_recorded_watering_atlas.png"
YEARLY_ATLASES = tuple(
    REPORT / f"maps/yearly/{year}_monthly_recorded_watering_atlas.png"
    for year in REFERENCE_YEARS
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class WateringTemporalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = (
            CALENDAR_LOR,
            CITY_MONTH,
            CITY_CALENDAR,
            SEASON,
            YEAR_SUMMARY,
            METADATA,
            TIMING_FIGURE,
            CALENDAR_ATLAS,
            ACTIVE_ATLAS,
            *YEARLY_ATLASES,
        )
        missing = [str(path) for path in required if not path.is_file()]
        if missing:
            raise AssertionError(
                "Temporal-atlas artifacts are missing; run "
                "pipelines/04_build_watering_temporal_atlas.py. Missing: "
                + ", ".join(missing)
            )
        cls.calendar_lor = read_rows(CALENDAR_LOR)
        cls.city_month = read_rows(CITY_MONTH)
        cls.city_calendar = read_rows(CITY_CALENDAR)
        cls.season = read_rows(SEASON)
        cls.year_summary = read_rows(YEAR_SUMMARY)
        cls.metadata = json.loads(METADATA.read_text(encoding="utf-8"))

    def test_calendar_climatology_is_balanced_complete_year_mean(self):
        self.assertEqual(REFERENCE_YEARS, (2021, 2022, 2023, 2024, 2025))
        self.assertEqual(ACTIVE_SEASON_MONTHS, (4, 5, 6, 7, 8, 9))
        self.assertEqual(len(self.calendar_lor), 542 * 12)
        self.assertEqual({len(row["bzr_id"]) for row in self.calendar_lor}, {6})
        foundation = read_rows(
            ROOT
            / "data/processed/foundation"
            / "lor_month_recorded_watering_2020_2025.csv"
        )
        source_keys = {(row["plr_id"], row["bzr_id"]) for row in foundation}
        output_keys = {(row["plr_id"], row["bzr_id"]) for row in self.calendar_lor}
        self.assertEqual(output_keys, source_keys)
        for month in range(1, 13):
            rows = [
                row for row in self.calendar_lor
                if int(row["calendar_month"]) == month
            ]
            with self.subTest(month=month):
                self.assertEqual(len(rows), 542)
                self.assertEqual({row["observed_complete_years"] for row in rows}, {"5"})
                self.assertEqual(len({row["plr_id"] for row in rows}), 542)

        may_events = sum(
            int(row["recorded_watering_events"])
            for row in self.calendar_lor
            if row["calendar_month"] == "5"
        )
        self.assertEqual(may_events, 5413)
        missing_denominator = sum(
            row["mean_monthly_recorded_events_per_1000_current_inventory_trees"] == ""
            for row in self.calendar_lor
        )
        self.assertEqual(missing_denominator, 2 * 12)

    def test_city_and_season_totals_are_additive(self):
        self.assertEqual(len(self.city_month), 68)
        self.assertEqual(
            sum(int(row["recorded_watering_events"]) for row in self.city_month),
            57786,
        )
        self.assertAlmostEqual(
            sum(float(row["recorded_litres"]) for row in self.city_month),
            2249502.0,
            places=6,
        )
        first = self.city_month[0]
        self.assertEqual(first["month"], "2020-05-01")
        self.assertEqual(first["platform_month_status"], "partial_platform_start")
        self.assertEqual(first["platform_live_days"], "14")

        self.assertEqual(len(self.city_calendar), 12)
        self.assertEqual(len(self.season), 4)
        reference_events = sum(
            int(row["recorded_watering_events"]) for row in self.city_calendar
        )
        seasonal_events = sum(
            int(row["recorded_watering_events"]) for row in self.season
        )
        self.assertEqual(reference_events, 41506)
        self.assertEqual(seasonal_events, reference_events)
        self.assertEqual(
            {int(row["observed_complete_months"]) for row in self.season}, {15}
        )
        self.assertEqual(
            {int(row["observed_complete_years"]) for row in self.season}, {5}
        )
        normalized_fields = {
            "mean_annual_season_recorded_events_per_1000_current_inventory_trees",
            "mean_annual_season_recorded_litres_per_current_inventory_tree",
            "mean_annual_season_recorded_litres_per_ha",
        }
        self.assertTrue(normalized_fields.issubset(self.season[0]))
        self.assertTrue(
            all(float(row[field]) >= 0 for row in self.season for field in normalized_fields)
        )

    def test_shared_map_scale_is_deterministic_and_semantic(self):
        breaks = tuple(self.metadata["map_scale"]["positive_break_values"])
        self.assertEqual(len(breaks), 5)
        self.assertTrue(all(left < right for left, right in zip(breaks, breaks[1:])))
        self.assertEqual(
            derive_shared_positive_breaks([1, 2, 3, 4, 5, 6, 7, 8]),
            (2.75, 4.5, 6.25, 7.3, 7.825),
        )
        self.assertEqual(classify_map_value(0, breaks), 0)
        self.assertEqual(classify_map_value(breaks[0], breaks), 1)
        self.assertEqual(classify_map_value(breaks[-1] + 1, breaks), 6)
        self.assertEqual(classify_map_value(math.nan, breaks), 7)
        with self.assertRaises(ValueError):
            classify_map_value(-0.1, breaks)
        self.assertTrue(self.metadata["map_scale"]["fixed_across_all_panels"])
        self.assertIn("No recorded", self.metadata["map_scale"]["class_labels"][0])
        self.assertIn("denominator", self.metadata["map_scale"]["class_labels"][-1])

    def test_seasons_outputs_and_claim_limits(self):
        self.assertEqual(season_for_month(1), "Winter")
        self.assertEqual(season_for_month(4), "Spring")
        self.assertEqual(season_for_month(7), "Summer")
        self.assertEqual(season_for_month(10), "Autumn")
        with self.assertRaises(ValueError):
            season_for_month(13)

        coverage = self.metadata["coverage"]
        self.assertTrue(coverage["partial_month_excluded_from_climatology"])
        self.assertEqual(coverage["climatology_complete_years"], list(REFERENCE_YEARS))
        self.assertIn("municipal", self.metadata["semantics"]["recorded_zero"])
        self.assertIn("do not estimate cooling", self.metadata["semantics"]["claim_boundary"])
        self.assertIn("tree-month", self.metadata["semantics"]["watered_tree_months"])
        self.assertIn("full Planungsraum", self.metadata["semantics"]["area_density_definition"])
        self.assertIn("not an irrigation", self.metadata["semantics"]["area_density_definition"])
        self.assertEqual(
            self.metadata["grains"]["season_summary"],
            "berlin_meteorological_season_pooled_2021_2025",
        )
        outputs = self.metadata["outputs"]
        for output_name, expected_hash in outputs["sha256"].items():
            with self.subTest(output=output_name):
                self.assertEqual(sha256(ROOT / outputs[output_name]), expected_hash)
        for path in (TIMING_FIGURE, CALENDAR_ATLAS, ACTIVE_ATLAS, *YEARLY_ATLASES):
            with self.subTest(path=path.name):
                self.assertGreater(path.stat().st_size, 100_000)

    def test_year_summary_matches_unpooled_source_months(self):
        source = read_rows(
            ROOT / "data/processed/foundation/lor_month_recorded_watering_2020_2025.csv"
        )
        self.assertEqual([int(row["year"]) for row in self.year_summary], list(REFERENCE_YEARS))
        for summary in self.year_summary:
            year = summary["year"]
            rows = [row for row in source if row["month"].startswith(year + "-")]
            positive = [row for row in rows if int(row["recorded_watering_events"]) > 0]
            with self.subTest(year=year):
                self.assertEqual(int(summary["observed_complete_months"]), 12)
                self.assertEqual(len(rows), 542 * 12)
                self.assertEqual(
                    int(summary["recorded_watering_events"]),
                    sum(int(row["recorded_watering_events"]) for row in rows),
                )
                self.assertAlmostEqual(
                    float(summary["recorded_litres"]),
                    sum(float(row["recorded_litres"]) for row in rows),
                )
                self.assertEqual(int(summary["lor_months_with_recorded_activity"]), len(positive))
                self.assertEqual(
                    int(summary["planungsraeume_with_recorded_activity"]),
                    len({row["plr_id"] for row in positive}),
                )
        self.assertEqual(sha256(YEAR_SUMMARY), sha256(REPORT / "tables" / YEAR_SUMMARY.name))
        self.assertEqual(self.metadata["audit"]["yearly_atlas_panels"], 60)
        self.assertEqual(self.metadata["audit"]["yearly_atlas_lor_months"], 542 * 60)
        self.assertEqual(self.metadata["coverage"]["yearly_atlas_years"], list(REFERENCE_YEARS))
        self.assertEqual(self.metadata["coverage"]["yearly_atlas_months_per_year"], list(range(1, 13)))
        self.assertIn("actual acquisition dates", self.metadata["semantics"]["temporal_alignment"])

    def test_public_build_runs_into_temporary_directories(self):
        import pandas as pd

        def fake_png(path: Path) -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"test" * 32)

        annual_inputs = []

        def capture_year(frame, lor, path, breaks, **kwargs):
            annual_inputs.append((frame.copy(), breaks, kwargs["metric"]))
            fake_png(path)

        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            processed = temporary / "processed"
            report = temporary / "report"
            with (
                patch.dict(
                    os.environ,
                    {"MPLCONFIGDIR": str(temporary / "matplotlib-cache")},
                ),
                patch(
                    "berlin_heat.watering_temporal._write_timing_figure",
                    side_effect=lambda frame, path, pd, np: fake_png(path),
                ),
                patch(
                    "berlin_heat.watering_temporal._write_calendar_atlas",
                    side_effect=lambda frame, lor, path, breaks: fake_png(path),
                ),
                patch(
                    "berlin_heat.watering_temporal._write_active_season_atlas",
                    side_effect=lambda frame, lor, path, breaks: fake_png(path),
                ),
                patch(
                    "berlin_heat.watering_temporal._write_monthly_atlas",
                    side_effect=capture_year,
                ),
            ):
                artifacts = build_watering_temporal_atlas(
                    ROOT,
                    processed_dir=processed,
                    output_dir=report,
                )
            self.assertEqual(artifacts.calendar_lor_rows, 542 * 12)
            rebuilt = read_rows(artifacts.calendar_lor_path)
            self.assertEqual({len(row["bzr_id"]) for row in rebuilt}, {6})
            self.assertTrue(artifacts.metadata_path.is_file())
            self.assertEqual(len(artifacts.yearly_atlas_paths), 5)
            self.assertTrue(all(path.is_file() for path in artifacts.yearly_atlas_paths))
            self.assertEqual(len(annual_inputs), 5)
            source = pd.read_csv(
                ROOT / "data/processed/foundation/lor_month_recorded_watering_2020_2025.csv",
                dtype={"plr_id": "string", "bzr_id": "string"},
                parse_dates=["month"],
            )
            metric = "recorded_events_per_1000_current_inventory_trees"
            columns = ["month", "plr_id", "recorded_watering_events", "recorded_litres", metric]
            for year, (frame, breaks, plotted_metric) in zip(REFERENCE_YEARS, annual_inputs):
                with self.subTest(year=year):
                    self.assertEqual(set(frame["year"]), {year})
                    self.assertEqual(set(frame["calendar_month"]), set(range(1, 13)))
                    self.assertEqual(plotted_metric, metric)
                    self.assertEqual(breaks, artifacts.map_breaks)
                    expected = source.loc[source["month"].dt.year.eq(year), columns]
                    pd.testing.assert_frame_equal(
                        frame[columns].sort_values(["month", "plr_id"]).reset_index(drop=True),
                        expected.sort_values(["month", "plr_id"]).reset_index(drop=True),
                    )

    def test_year_atlas_rejects_mixed_years_and_missing_months(self):
        import pandas as pd

        frame = pd.DataFrame([
            {"year": 2021, "calendar_month": month, "plr_id": plr, "recorded_watering_events": 1}
            for month in range(1, 13) for plr in ("01", "02")
        ])
        lor = pd.DataFrame({"plr_id": ["01", "02"]})
        with patch("berlin_heat.watering_temporal._write_monthly_atlas") as writer:
            _write_year_atlas(frame, lor, Path("unused.png"), (1.0,), 2021)
            writer.assert_called_once()
            mixed = frame.copy()
            mixed.loc[0, "year"] = 2022
            for invalid in (mixed, frame.iloc[:-1], pd.concat([frame.iloc[1:], frame.iloc[[1]]])):
                with self.assertRaisesRegex(ValueError, "complete, unmixed year"):
                    _write_year_atlas(invalid, lor, Path("unused.png"), (1.0,), 2021)


    def test_panel_validation_rejects_mixed_status_and_negative_values(self):
        import pandas as pd

        panel = pd.read_csv(
            ROOT
            / "data/processed/foundation"
            / "lor_month_recorded_watering_2020_2025.csv",
            dtype={"plr_id": "string", "bzr_id": "string"},
            parse_dates=["month"],
        )
        _validate_panel(panel, pd)

        mixed_status = panel.copy()
        mixed_status.loc[0, "platform_month_status"] = "complete_month"
        with self.assertRaises(ValueError):
            _validate_panel(mixed_status, pd)

        negative = panel.copy()
        negative.loc[0, "recorded_watering_events"] = -1
        with self.assertRaises(ValueError):
            _validate_panel(negative, pd)


if __name__ == "__main__":
    unittest.main()
