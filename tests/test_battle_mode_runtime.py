"""Mode attribution enriches own result metadata without changing any credits."""
import copy
import unittest
from unittest.mock import patch

from core import EconomyLedger
from capture.native import derive_credits
from capture.normalizer import normalize_snapshot
from capture.snapshot import make_snapshot
from capture.storage import read_json
from test_native_finance import Reusable
import test_capture_runtime as harness


def mode_snapshot(code=20):
    raw = harness.fixture()
    raw['common'].update(bonusType=code, guiType=15)
    snapshot = make_snapshot(raw, 'NA')
    snapshot['native_credits'] = derive_credits(raw, lambda _: Reusable())
    return snapshot


class BattleModeRuntimeTests(unittest.TestCase):
    setUp = harness.RuntimeTests.setUp
    tearDown = harness.RuntimeTests.tearDown

    def legacy(self):
        snapshot = mode_snapshot()
        record = normalize_snapshot(snapshot)
        record.pop('battle_mode', None)
        self.collector.ledger.upsert_result(record)
        self.collector.ledger.save(self.collector.ledger_path)
        return snapshot

    def test_native_event_captures_persists_and_presents_mode_with_same_financial_total(self):
        raw = harness.fixture()
        raw['common'].update(bonusType=20, guiType=15)
        with patch.object(self.collector, '_vehicle_item', return_value=None):
            self.events.onBattleResultsReceived.emit(True, raw)
            self.events.onBattleResultsReceived.emit(True, raw)
            payload = self.collector.panel_payload()
        self.assertEqual(payload['history'][0]['battle_mode']['label'], 'Escaramuza')
        self.assertEqual(payload['history'][0]['battle_mode']['bonus_type'], 20)
        self.assertEqual(payload['summary']['battle_count'], 1)
        self.assertEqual(payload['summary']['gross_credits'], 80500)
        self.assertEqual(payload['summary']['net_credits'], 51500)
        self.assertEqual(read_json(self.collector.ledger_path)['records'][0]['battle_mode']['bonus_type'], 20)

    def test_legacy_capture_supplies_only_missing_own_mode_metadata(self):
        snapshot = self.legacy()
        self.collector.store.save(snapshot)
        before = self.collector.ledger.list_results()[0]
        before_totals = self.collector.ledger.summary('NA', '101')
        before_config = copy.deepcopy(self.collector.config)
        with patch.object(self.collector, '_vehicle_item', return_value=None):
            payload = self.collector.panel_payload()
        after = self.collector.ledger.list_results()[0]
        self.assertEqual(after['battle_mode'], {'bonus_type': 20, 'gui_type': 15})
        for field in before:
            if field != 'battle_mode':
                self.assertEqual(after[field], before[field])
        self.assertEqual(self.collector.ledger.summary('NA', '101'), before_totals)
        self.assertEqual(self.collector.config, before_config)
        self.assertEqual(payload['history'][0]['battle_mode']['label'], 'Escaramuza')

    def test_foreign_missing_or_invalid_context_does_not_guess_a_mode(self):
        snapshot = self.legacy()
        foreign = copy.deepcopy(snapshot)
        foreign['account_id'] = '999'
        wrong_region = copy.deepcopy(snapshot)
        wrong_region['region'] = 'EU'
        malformed = copy.deepcopy(snapshot)
        malformed['common'] = {'bonusType': '20', 'guiType': 15}
        for snapshots in ([foreign], [wrong_region], [], [malformed]):
            with patch.object(self.collector, '_vehicle_item', return_value=None):
                self.collector._enrich_vehicle_history('101', snapshots)
            self.assertIsNone(self.collector.ledger.list_results()[0].get('battle_mode'))

    def test_failed_metadata_save_keeps_ledger_in_memory_and_can_retry(self):
        snapshot = self.legacy()
        before = self.collector.ledger.to_dict()
        before_disk = read_json(self.collector.ledger_path)
        with patch.object(self.collector, '_vehicle_item', return_value=None):
            with patch.object(EconomyLedger, 'save', side_effect=OSError('synthetic')):
                self.collector._enrich_vehicle_history('101', [snapshot])
            self.assertEqual(self.collector.ledger.to_dict(), before)
            self.assertEqual(read_json(self.collector.ledger_path), before_disk)
            self.collector._enrich_vehicle_history('101', [snapshot])
        self.assertEqual(self.collector.ledger.list_results()[0]['battle_mode']['bonus_type'], 20)

    def test_known_mode_is_not_overwritten_from_an_older_saved_snapshot(self):
        snapshot = mode_snapshot()
        record = normalize_snapshot(snapshot)
        self.collector.ledger.upsert_result(record)
        stale = mode_snapshot(1)
        with patch.object(self.collector, '_vehicle_item', return_value=None):
            self.collector._enrich_vehicle_history('101', [stale])
        self.assertEqual(self.collector.ledger.list_results()[0]['battle_mode']['bonus_type'], 20)


if __name__ == '__main__':
    unittest.main()
