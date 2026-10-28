import copy
import os
import shutil
import tempfile
import unittest

from capture.storage import CaptureStore, read_json
from capture.snapshot import make_snapshot
from test_snapshot import fixture


class CaptureStorageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="credit-ledger-test-")
        self.store = CaptureStore(self.directory)

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_duplicate_different_capture_time_is_one_file(self):
        first = make_snapshot(fixture(), "NA")
        action, path = self.store.save(first)
        self.assertEqual(action, "inserted")
        later = copy.deepcopy(first)
        later["captured_at"] = "2026-10-17T23:59:00Z"
        later["source"] = "cache"
        self.assertEqual(self.store.save(later)[0], "unchanged")
        self.assertEqual(read_json(path), first)

    def test_correction_replaces_existing_capture(self):
        snapshot = make_snapshot(fixture(), "NA")
        _, path = self.store.save(snapshot)
        snapshot["personal"]["vehicles"][0]["fields"]["autoRepairCost"] = 123
        self.assertEqual(self.store.save(snapshot)[0], "updated")
        self.assertEqual(read_json(path)["personal"]["vehicles"][0]["fields"]["autoRepairCost"], 123)

    def test_paths_cannot_escape_capture_directory(self):
        for field in ["region", "account_id", "battle_id"]:
            snapshot = make_snapshot(fixture(), "NA")
            snapshot[field] = "../outside"
            with self.assertRaises(ValueError):
                self.store.save(snapshot)

    def test_accounts_and_regions_are_separate(self):
        snapshot = make_snapshot(fixture(), "NA")
        _, first = self.store.save(snapshot)
        snapshot["account_id"] = "102"
        _, second = self.store.save(snapshot)
        snapshot["region"] = "EU"
        _, third = self.store.save(snapshot)
        self.assertEqual(len(set([first, second, third])), 3)
        self.assertTrue(all(os.path.isfile(path) for path in [first, second, third]))


if __name__ == "__main__":
    unittest.main()
