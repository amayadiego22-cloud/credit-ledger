"""Old mode attribution is bounded, account-scoped and independent of credits."""
import copy
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from capture import storage
from capture.storage import CaptureStore, atomic_json
from capture.snapshot import make_snapshot
from capture.normalizer import normalize_snapshot
from capture.native import derive_credits
from test_native_finance import Reusable
import test_capture_runtime as harness


def captured(identity, code=20):
    raw = harness.fixture()
    raw['arenaUniqueID'] = int(identity)
    raw['common']['bonusType'] = code
    snapshot = make_snapshot(raw, 'NA')
    snapshot['native_credits'] = derive_credits(raw, lambda _: Reusable())
    return snapshot


class ModeMetadataStorageTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix='credit-ledger-mode-filter-')
        self.store = CaptureStore(self.directory)

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_bounded_rotating_reads_cache_only_copied_mode_context(self):
        for identity in ('1', '2', '3'):
            self.store.save(captured(identity))
        with patch.object(storage, 'read_json', wraps=storage.read_json) as read:
            seen = set()
            for _ in range(3):
                rows = self.store.mode_metadata('NA', '101', ['1', '2', '3'], read_limit=1)
                seen.update(row['battle_id'] for row in rows)
            self.assertEqual(seen, {'1', '2', '3'})
            self.assertEqual(read.call_count, 3)
            rows[0]['common']['bonusType'] = 999
            rows = self.store.mode_metadata('NA', '101', ['1', '2', '3'], read_limit=1)
            self.assertEqual(read.call_count, 3)
            self.assertTrue(all(row['common']['bonusType'] == 20 for row in rows))
            self.assertTrue(all(set(row) == {'region', 'account_id', 'battle_id', 'common'} for row in rows))

    def test_signature_changes_previous_journal_and_foreign_content_are_checked(self):
        snapshot = captured('1')
        _, path = self.store.save(snapshot)
        foreign = copy.deepcopy(snapshot)
        foreign['account_id'] = '999'
        atomic_json(path, foreign)
        self.assertEqual(self.store.mode_metadata('NA', '101', ['1']), [])
        atomic_json(path, snapshot)
        os.utime(path, (1900000000, 1900000000))
        self.assertEqual(self.store.mode_metadata('NA', '101', ['1'])[0]['common']['bonusType'], 20)
        os.rename(path, path + '.previous')
        self.assertEqual(self.store.mode_metadata('NA', '101', ['1'])[0]['battle_id'], '1')
        self.assertEqual(self.store.mode_metadata('NA', '202', ['1']), [])
        self.assertEqual(self.store.mode_metadata('NA', '101', ['../../1']), [])

    def test_corrupt_capture_does_not_starve_valid_context_and_can_be_repaired(self):
        _, bad_path = self.store.save(captured('1'))
        self.store.save(captured('2', 43))
        with open(bad_path, 'w') as handle:
            handle.write('{broken')
        self.assertEqual(self.store.mode_metadata('NA', '101', ['1', '2'], read_limit=1), [])
        rows = self.store.mode_metadata('NA', '101', ['1', '2'], read_limit=1)
        self.assertEqual(rows[0]['common']['bonusType'], 43)
        atomic_json(bad_path, captured('1', 1))
        os.utime(bad_path, (1900000000, 1900000000))
        rows = self.store.mode_metadata('NA', '101', ['1', '2'], read_limit=1)
        self.assertIn('1', [row['battle_id'] for row in rows])


class ModeFilterRuntimeTests(unittest.TestCase):
    setUp = harness.RuntimeTests.setUp
    tearDown = harness.RuntimeTests.tearDown

    def test_old_mode_beyond_global100_is_recovered_and_enters_complete_mode_summary(self):
        older = captured('1', 20)
        old_record = normalize_snapshot(older)
        old_record['battle_mode'] = None
        self.collector.ledger.upsert_result(old_record)
        self.collector.store.save(older)
        for identity in range(2, 103):
            recent = normalize_snapshot(captured(str(identity), 1))
            recent['occurred_at'] = '2026-10-19T12:00:00Z'
            self.collector.ledger.upsert_result(recent)
        self.collector.ledger.save(self.collector.ledger_path)
        before = self.collector.ledger.summary('NA', '101')
        with patch.object(self.collector, '_vehicle_item', return_value=None), \
                patch.object(self.collector.store, 'recovery_candidates', return_value=[]):
            payload = self.collector.panel_payload()
        groups = dict((group['key'], group) for group in payload['mode_groups'])
        self.assertEqual(groups['mode:20']['summary']['net_credits'], 51500)
        self.assertEqual(groups['mode:20']['history'][0]['battle_id'], '1')
        self.assertNotIn('1', [row['battle_id'] for row in payload['history']])
        self.assertEqual(self.collector.ledger.summary('NA', '101'), before)
        self.assertEqual(payload['summary']['battle_count'], 102)


if __name__ == '__main__':
    unittest.main()
