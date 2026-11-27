"""Street-pump status parsing, change dating, season panel and snapshot safeguards."""
from datetime import date
import gzip
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from berlin_heat import pump_status as ps

ROOT = Path(__file__).resolve().parents[1]
END = pd.Timestamp("2026-07-27T09:00:00Z")
NET = {"man_made": "water_well", "network": ps.PLATFORM_NETWORK}


def feature(osm_id, version, valid_from, valid_to, lon=13.40, lat=52.52, **tags):
    tags = {key.replace("__", ":"): value for key, value in tags.items()}
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {"@osmId": osm_id, "@version": version, "@changesetId": 100 + version,
                           "@validFrom": valid_from, "@validTo": valid_to, **tags}}


def pump_history():
    """One pump: unknown, reported working, failure, repair at 00:30 Berlin, short failure, deletion."""
    desc = {"man_made": "water_well", "description": ps.PLATFORM_NETWORK}
    return [
        feature("node/1", 1, "2019-01-10T10:00:00Z", "2020-05-05T10:00:00Z", **desc),
        feature("node/1", 2, "2020-05-05T10:00:00Z", "2021-06-15T10:00:00Z",
                **desc, pump__status="ok", check_date="2020-05-04"),
        feature("node/1", 3, "2021-06-15T10:00:00Z", "2022-03-31T22:30:00Z",
                **NET, pump__status="broken", check_date="2020-05-04"),
        feature("node/1", 4, "2022-03-31T22:30:00Z", "2022-08-01T10:00:00Z",
                **NET, pump__status="ok", check_date="2022-03-30"),
        feature("node/1", 5, "2022-08-01T10:00:00Z", "2022-08-05T10:00:00Z",
                **NET, pump__status="missing_beam", check_date="2022-03-30"),
        feature("node/1", 6, "2022-08-05T10:00:00Z", "2023-05-01T10:00:00Z",
                **NET, pump__status="ok", check_date="2022-03-30"),
    ]


def history_tables(features):
    versions = ps.versions_from_features(features)
    segments = ps.status_segments(versions, END)
    return versions, segments, ps.status_changes(segments, END)


class StatusParsingTests(unittest.TestCase):
    def test_platform_status_codes_and_variants(self):
        expected = {"ok": "working", "OK": "working", "o k.": "working", "broken": "broken",
                    "missing_beam": "broken", "out_of_order": "broken", "locked": "locked",
                    "blocked": "locked", "missing": "removed"}
        for value, status in expected.items():
            with self.subTest(value=value):
                reading = ps.parse_status({"man_made": "water_well", "pump:status": value})
                self.assertEqual((reading.status, reading.source), (status, "pump:status"))
        self.assertEqual(ps.parse_status({"man_made": "water_well", "pump:status": "ok"}).usable, 1)
        self.assertEqual(ps.parse_status({"man_made": "water_well", "pump:status": "locked"}).usable, 0)

    def test_free_text_uses_explicit_table_and_unknown_text_is_not_guessed(self):
        self.assertEqual(ps.parse_status({"man_made": "water_well", "pump:status": "Abgebaut"}).status,
                         "removed")
        self.assertEqual(ps.parse_status({"man_made": "water_well",
                                          "pump:status": "funktioniert, aber geringe Hubleistung"}).status,
                         "working")
        reading = ps.parse_status({"man_made": "water_well", "pump:status": "off"})
        self.assertEqual((reading.status, reading.raw_value, reading.usable), ("unrecognised", "off", None))
        self.assertEqual(ps.parse_status({"man_made": "water_well"}).status, "unknown")
        self.assertIsNone(ps.parse_status({"man_made": "water_well"}).usable)

    def test_lifecycle_prefix_overrides_stale_status(self):
        cases = [({"removed:man_made": "water_well", "pump:status": "broken"}, "removed"),
                 ({"razed:man_made": "water_well"}, "removed"),
                 ({"was:man_made": "water_well"}, "removed"),
                 ({"disused:man_made": "water_well", "pump:status": "ok"}, "disused"),
                 ({"abandoned:man_made": "water_well"}, "disused"),
                 ({"man_made": "disused:water_well"}, "disused"),
                 ({"man_made": "monitoring_station", "removed:man_made": "water_well"}, "removed"),
                 ({"man_made": "pumping_station"}, "not_a_pump"),
                 ({"amenity": "drinking_water"}, "not_a_pump")]
        for tags, status in cases:
            with self.subTest(tags=tags):
                self.assertEqual(ps.parse_status(tags).status, status)
        self.assertEqual(ps.parse_status({"removed:man_made": "water_well"}).source, "removed:man_made")

    def test_secondary_keys_and_flags_only_fill_gaps(self):
        well = {"man_made": "water_well"}
        self.assertEqual(ps.parse_status({**well, "pump:status": "ok", "operational_status": "broken"}).status,
                         "working")
        reading = ps.parse_status({**well, "pump_status": "ok"})
        self.assertEqual((reading.status, reading.source), ("working", "pump_status"))
        self.assertEqual(ps.parse_status({**well, "status": "damaged"}).status, "broken")
        self.assertEqual(ps.parse_status({**well, "pump:status": "off", "operational:status": "working"}).source,
                         "operational:status")
        self.assertEqual(ps.parse_status({**well, "locked": "yes"}).status, "locked")
        self.assertEqual(ps.parse_status({**well, "disused": "yes"}).status, "disused")
        self.assertEqual(ps.parse_status({**well, "pump": "no"}).status, "pump_absent")
        self.assertEqual(ps.parse_status({**well, "removed:pump": "manual"}).status, "pump_absent")
        self.assertEqual(ps.parse_status({**well, "pump": "no", "pump:status": "ok"}).status, "working")

    def test_platform_label_replicates_harvester_mapping(self):
        self.assertEqual(ps.platform_label({"pump:status": "ok"}), "funktionsfähig")
        self.assertEqual(ps.platform_label({"pump:status": "missing_beam"}), "defekt")
        self.assertEqual(ps.platform_label({"pump:status": "blocked"}), "verriegelt")
        self.assertEqual(ps.platform_label({}), "unbekannt")
        self.assertEqual(ps.platform_label({"pump:status": "OK"}), "OK")

    def test_check_date_formats_and_precision(self):
        cases = {"2023-06-04": (date(2023, 6, 4), "day"), "1.8.2022": (date(2022, 8, 1), "day"),
                 "06.06.2026": (date(2026, 6, 6), "day"), "2022-09": (date(2022, 9, 1), "month"),
                 "2018": (date(2018, 1, 1), "year")}
        for raw, (value, precision) in cases.items():
            with self.subTest(raw=raw):
                parsed = ps.parse_check_date(raw)
                self.assertEqual((parsed.value, parsed.precision), (value, precision))
        for raw in ("10-22", "2022-02-30", "", None, "ok"):
            with self.subTest(raw=raw):
                self.assertIsNone(ps.parse_check_date(raw))

    def test_change_typology(self):
        cases = {("broken", "working"): "repair", ("locked", "working"): "repair",
                 ("working", "removed"): "failure", ("working", "pump_absent"): "failure",
                 ("unknown", "working"): "status_reported", ("working", "unknown"): "status_withdrawn",
                 ("broken", "locked"): "reclassified", ("unknown", "unrecognised"): "reclassified",
                 ("working", "deleted"): "exit", ("working", "not_a_pump"): "exit",
                 ("deleted", "working"): "reentry"}
        for (before, after), change_type in cases.items():
            with self.subTest(before=before, after=after):
                self.assertEqual(ps.classify_change(before, after), change_type)


class HistoryTests(unittest.TestCase):
    def test_segments_mark_deletions_and_changes_are_typed(self):
        _, segments, changes = history_tables(pump_history())
        self.assertEqual(segments["status"].tolist(),
                         ["unknown", "working", "broken", "working", "broken", "working", "deleted"])
        self.assertEqual(segments.iloc[-1]["segment_end"], END)
        self.assertEqual(changes["change_type"].tolist(),
                         ["status_reported", "failure", "repair", "failure", "repair", "exit"])
        self.assertEqual(changes["check_date_backed"].tolist(), [True, False, True, False, False, False])

    def test_check_date_dating_and_berlin_edit_dates(self):
        _, _, changes = history_tables(pump_history())
        repair = changes.iloc[2]
        self.assertEqual(repair["edit_date"], date(2022, 4, 1))  # 22:30 UTC is 00:30 in Berlin
        self.assertEqual(repair["check_date_lag_days"], 2)
        self.assertEqual((repair["event_date"], repair["event_date_basis"]), (date(2022, 3, 30), "check_date"))
        failure = changes.iloc[1]
        self.assertEqual((failure["event_date"], failure["event_date_basis"]), (date(2021, 6, 15), "edit"))

    def test_reverts_durations_and_censoring(self):
        _, _, changes = history_tables(pump_history())
        short = changes.iloc[3]
        self.assertTrue(short["reverted_within_14d"])
        self.assertEqual(short["new_status_days"], 4.0)
        self.assertFalse(changes.iloc[2]["reverted_within_14d"])
        self.assertTrue(changes.iloc[-1]["right_censored"])
        self.assertFalse(changes.iloc[0]["right_censored"])

    def test_check_date_backing_window_and_two_step_edits(self):
        def one_change(check_version, check_date):
            features = [feature("node/9", 1, "2023-01-01T10:00:00Z", "2023-06-01T08:00:00Z",
                                **NET, pump__status="ok", check_date="2022-01-01"),
                        feature("node/9", 2, "2023-06-01T08:00:00Z", "2023-06-01T10:00:00Z",
                                **NET, pump__status="ok",
                                check_date=check_date if check_version == 2 else "2022-01-01"),
                        feature("node/9", 3, "2023-06-01T10:00:00Z", "2026-07-27T09:00:00Z",
                                **NET, pump__status="broken",
                                check_date=check_date if check_version in (2, 3) else "2022-01-01")]
            return history_tables(features)[2].iloc[0]
        self.assertTrue(one_change(2, "2023-06-01")["check_date_backed_day"])  # set two hours earlier
        self.assertTrue(one_change(3, "2023-05-20")["check_date_backed"])
        self.assertFalse(one_change(3, "2022-05-01")["check_date_backed"])  # more than 365 days old
        self.assertFalse(one_change(3, "2023-06-05")["check_date_backed"])  # after the edit
        self.assertFalse(one_change(1, "2022-01-01")["check_date_backed"])  # unchanged old date
        coarse = one_change(3, "2023")
        self.assertTrue(coarse["check_date_backed"])
        self.assertFalse(coarse["check_date_backed_day"])
        self.assertEqual(coarse["event_date_basis"], "edit")

    def test_leading_non_pump_versions_are_unmapped_and_restorations_carry_net_change(self):
        features = [feature("node/7", 1, "2019-01-01T00:00:00Z", "2020-01-01T00:00:00Z", amenity="drinking_water"),
                    feature("node/7", 2, "2020-01-01T00:00:00Z", "2022-07-28T10:00:00Z", **NET, pump__status="ok"),
                    feature("node/7", 4, "2022-09-09T10:00:00Z", "2026-07-27T09:00:00Z",
                            removed__man_made="water_well", network=ps.PLATFORM_NETWORK)]
        _, segments, changes = history_tables(features)
        self.assertEqual(segments["status"].tolist(), ["working", "deleted", "removed"])
        self.assertEqual(changes["change_type"].tolist(), ["exit", "reentry"])
        self.assertEqual(changes.iloc[0]["net_change_if_restored"], "failure")
        self.assertTrue(pd.isna(changes.iloc[1]["net_change_if_restored"]))
        panel = ps.season_panel(["node/7"], segments, changes, seasons=[2019, 2022]).set_index("season")
        self.assertEqual(panel.loc[2019, "status_at_start"], "not_mapped")
        self.assertEqual((panel.loc[2022, "n_exit"], panel.loc[2022, "n_reentry"], panel.loc[2022, "n_failure"]),
                         (1, 1, 0))

    def test_overlapping_versions_are_rejected(self):
        features = [feature("node/5", 1, "2020-01-01T00:00:00Z", "2021-01-01T00:00:00Z", **NET),
                    feature("node/5", 2, "2020-06-01T00:00:00Z", "2022-01-01T00:00:00Z", **NET)]
        with self.assertRaises(ValueError):
            ps.status_segments(ps.versions_from_features(features), END)


class PanelTests(unittest.TestCase):
    def test_season_panel_uses_berlin_midnight_and_counts_in_season_changes(self):
        late = [feature("node/2", 1, "2022-06-01T10:00:00Z", "2026-07-27T09:00:00Z", **NET, pump__status="ok")]
        _, segments, changes = history_tables(pump_history() + late)
        panel = ps.season_panel(["node/1", "node/2"], segments, changes, seasons=[2019, 2021, 2022, 2023])
        self.assertEqual(len(panel), 8)
        row = panel.set_index(["osm_id", "season"])
        y22 = row.loc[("node/1", 2022)]
        self.assertEqual(y22["status_at_start"], "broken")  # repair edited at 00:30 on 1 April
        self.assertEqual((y22["n_repair"], y22["n_failure"], y22["n_status_changes"]), (2, 1, 3))
        self.assertEqual(y22["first_repair_date"], date(2022, 4, 1))
        self.assertEqual(y22["status_path"], "broken>working>broken>working")
        self.assertTrue(y22["repair_or_failure"] and y22["repair_or_failure_check_backed"])
        self.assertEqual(y22["n_check_date_updates"], 1)
        y21 = row.loc[("node/1", 2021)]
        self.assertEqual((y21["status_at_start"], y21["status_at_end"], y21["n_failure"]),
                         ("working", "broken", 1))
        self.assertFalse(y21["repair_or_failure_check_backed"])
        self.assertTrue(y21["platform_visible_at_start"])  # description selector before May 2021
        self.assertEqual(row.loc[("node/1", 2019), "status_at_start"], "unknown")
        self.assertEqual(row.loc[("node/1", 2023), "status_at_end"], "deleted")
        self.assertEqual(row.loc[("node/1", 2023), "n_exit"], 1)
        new = row.loc[("node/2", 2022)]
        self.assertEqual((new["status_at_start"], new["mapped_in_season"], new["status_path"]),
                         ("not_mapped", True, "not_mapped>working"))
        self.assertTrue(pd.isna(new["usable_at_start"]))
        self.assertEqual(new["n_status_changes"], 0)

    def test_platform_visibility_follows_selector_switch(self):
        features = [feature("node/3", 1, "2020-01-01T00:00:00Z", "2026-07-27T09:00:00Z",
                            man_made="water_well", description=ps.PLATFORM_NETWORK)]
        _, segments, _ = history_tables(features)
        before = ps.status_at(segments, pd.Timestamp("2021-04-01T00:00:00Z"))
        after = ps.status_at(segments, pd.Timestamp("2022-04-01T00:00:00Z"))
        self.assertTrue(before.loc["node/3", "platform_visible"])
        self.assertFalse(after.loc["node/3", "platform_visible"])

    def test_deletion_with_nearby_new_node_is_flagged_as_remapping(self):
        successor = [feature("node/2", 1, "2023-05-10T10:00:00Z", "2026-07-27T09:00:00Z",
                             lon=13.40003, **NET, pump__status="ok")]
        _, segments, changes = history_tables(pump_history() + successor)
        register = pd.DataFrame({"osm_id": ["node/1", "node/2"], "x_25833": [392000.0, 392002.0],
                                 "y_25833": [5820000.0, 5820000.0],
                                 "first_mapped_utc": pd.to_datetime(["2019-01-10T10:00:00Z",
                                                                     "2023-05-10T10:00:00Z"], utc=True)})
        flagged = ps.attach_successors(changes, segments, register)
        exit_row = flagged[flagged["change_type"].eq("exit")].iloc[0]
        self.assertEqual((exit_row["successor_osm_id"], exit_row["successor_relation"]),
                         ("node/2", "new_node_within_31d"))
        far = register.assign(x_25833=[392000.0, 392500.0])
        self.assertTrue(ps.attach_successors(changes, segments, far)["successor_osm_id"].isna().all())

    def test_register_keeps_only_platform_nodes_inside_berlin(self):
        import geopandas as gpd
        from shapely.geometry import box

        lor = gpd.GeoDataFrame({"plr_id": ["01100101"], "bzr_id": ["011001"], "district": ["Mitte"]},
                               geometry=[box(385000, 5815000, 395000, 5825000)], crs=ps.ANALYSIS_CRS)
        features = [feature("node/1", 1, "2019-01-01T00:00:00Z", "2026-07-27T09:00:00Z",
                            man_made="water_well", description=ps.PLATFORM_NETWORK),
                    feature("node/2", 1, "2019-01-01T00:00:00Z", "2026-07-27T09:00:00Z",
                            man_made="water_well"),
                    feature("node/3", 1, "2019-01-01T00:00:00Z", "2026-07-27T09:00:00Z",
                            lon=13.90, **NET)]
        register = ps.pump_register(ps.versions_from_features(features), lor).set_index("osm_id")
        self.assertEqual(register.index[register["in_universe"]].tolist(), ["node/1"])
        self.assertFalse(register.loc["node/3", "in_berlin"])
        self.assertEqual(register.loc["node/1", "plr_id"], "01100101")


class FeasibilityTests(unittest.TestCase):
    def test_tree_counts_include_the_radius(self):
        trees = np.array([[50.0, 0.0], [100.0, 0.0], [150.0, 0.0], [200.0, 0.0], [200.5, 0.0]])
        counts = ps.trees_within(np.array([[0.0, 0.0]]), trees)
        self.assertEqual((counts.loc[0, "street_trees_100m"], counts.loc[0, "street_trees_200m"]), (2, 4))

    def test_comparison_trees_exclude_trees_near_treated_pumps(self):
        panel = pd.DataFrame({"osm_id": ["node/1", "node/2", "node/3"], "season": 2022,
                              "n_repair": [1, 0, 0], "n_failure": [0, 0, 0],
                              "repair_or_failure": [True, False, False],
                              "repair_or_failure_check_backed": [False, False, False],
                              "mapped_at_start": [True, True, True],
                              "usable_at_start": pd.array([0, 1, pd.NA], dtype="Int64"),
                              "n_status_changes": [1, 0, 0],
                              "status_at_end": ["working", "working", "unknown"]})
        positions = pd.DataFrame({"osm_id": ["node/1", "node/2", "node/3"],
                                  "x_25833": [0.0, 150.0, 1000.0], "y_25833": [0.0, 0.0, 0.0]})
        trees = np.array([[75.0, 0.0], [160.0, 0.0], [1000.0, 10.0]])
        table = ps.design_feasibility(panel, positions, trees).set_index("group")
        self.assertEqual(table.loc["repair", "pumps"], 1)
        self.assertEqual(table.loc["repair", "trees_within_100m"], 1)
        comparison = table.loc["unchanged_comparison"]
        self.assertEqual(comparison["pumps"], 1)  # node/3 has no known start status
        self.assertEqual((comparison["trees_within_100m"], comparison["trees_within_100m_also_near_treated"]),
                         (1, 1))
        self.assertEqual(comparison["trees_within_200m"], 0)


class SnapshotTests(unittest.TestCase):
    def test_frozen_archives_are_deterministic_and_verified(self):
        payload = json.dumps({"features": []}).encode()
        frozen = ps.freeze_bytes(payload)
        self.assertEqual(frozen, ps.freeze_bytes(payload))
        self.assertEqual(frozen[4:8], b"\x00\x00\x00\x00")  # gzip mtime 0
        self.assertEqual(gzip.decompress(frozen), payload)
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "part.gz").write_bytes(frozen)
            info = {"archive": "part.gz", "archive_sha256": ps._sha256_bytes(frozen),
                    "response_sha256": ps._sha256_bytes(payload)}
            self.assertEqual(ps.read_frozen(folder, info), {"features": []})
            (folder / "part.gz").write_bytes(ps.freeze_bytes(payload + b" "))
            with self.assertRaises(ValueError):
                ps.read_frozen(folder, info)

    def test_existing_snapshot_is_never_replaced_implicitly(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / ps.SNAPSHOT_DIR
            folder.mkdir(parents=True)
            (folder / "snapshot.json").write_text("{}")
            with self.assertRaises(FileExistsError):
                ps.download_snapshot(Path(directory))

    def test_history_chunks_cover_ids_in_order(self):
        ids = [f"node/{number}" for number in range(1, 1206)]
        chunks = ps.history_chunks(ids)
        self.assertEqual([len(chunk) for chunk in chunks], [500, 500, 205])
        self.assertEqual(sum(chunks, []), ids)

    def test_treatment_build_never_reads_watering_outcomes(self):
        source = (ROOT / "src/berlin_heat/pump_status.py").read_text(encoding="utf-8")
        for marker in ("giessdenkiez_bewässerungsdaten", "recorded_watering_events", "recorded_tree_day",
                       "lor_day_recorded_watering", "bewaesserungsmenge", "pflanzjahr", "standalter"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, source)


if __name__ == "__main__":
    unittest.main()
