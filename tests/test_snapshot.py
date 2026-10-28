# -*- coding: utf-8 -*-
import copy
import json
import unittest

from capture.snapshot import SnapshotError, make_snapshot


def fixture():
    # Synthetic data only, not a recorded game response.
    return {"arenaUniqueID": 1234567890123456789,
            "personal": {"avatar": {"accountDBID": 101, "credits": 500,
                                    "name": "PRIVATE-NAME"},
                         321: {"originalCredits": 80000, "autoRepairCost": 8000,
                               "creditsReplay": b"\x01\x00\x01\x00\x00\x00",
                               "autoLoadCost": (12000, 0),
                               "autoEquipCost": (9000, 0, 0),
                               "damageDealt": 2000}},
            "players": {999: {"name": "OTHER-PLAYER"}},
            "common": {"arenaCreateTime": 1792242000, "duration": 300}}


class SnapshotTests(unittest.TestCase):
    def test_own_economy_only_and_exact_identity(self):
        result = make_snapshot(fixture(), "na")
        encoded = json.dumps(result)
        self.assertNotIn("PRIVATE-NAME", encoded)
        self.assertNotIn("OTHER-PLAYER", encoded)
        self.assertNotIn("damageDealt", result["personal"]["vehicles"][0]["fields"])
        self.assertEqual(result["battle_id"], "1234567890123456789")
        self.assertEqual(result["account_id"], "101")
        self.assertEqual(result["region"], "NA")
        self.assertEqual(result["personal"]["vehicles"][0]["fields"]["autoLoadCost"], [12000, 0])
        self.assertEqual(result["personal"]["vehicles"][0]["fields"]["creditsReplay"]["encoding"], "base64")

    def test_avatar_first_or_last_does_not_select_it_as_vehicle(self):
        result = make_snapshot(fixture(), "NA")
        self.assertEqual(len(result["personal"]["vehicles"]), 1)
        self.assertEqual(result["personal"]["vehicles"][0]["vehicle_type_id"], "321")

    def test_multiple_vehicles_kept_separate_without_double_summing(self):
        raw = fixture()
        raw["personal"][654] = {"originalCredits": 20000}
        result = make_snapshot(raw, "NA")
        self.assertEqual(len(result["personal"]["vehicles"]), 2)
        self.assertEqual(result["reconciliation"]["status"], "unverified")

    def test_unidentified_or_malformed_result_is_rejected(self):
        for value in [None, {}, {"arenaUniqueID": True}]:
            with self.assertRaises(SnapshotError):
                make_snapshot(value, "NA")
        raw = fixture()
        del raw["personal"]["avatar"]["accountDBID"]
        with self.assertRaises(SnapshotError):
            make_snapshot(raw, "NA")

    def test_input_is_not_mutated(self):
        raw = fixture()
        original = copy.deepcopy(raw)
        make_snapshot(raw, "NA")
        self.assertEqual(raw, original)


if __name__ == "__main__":
    unittest.main()
