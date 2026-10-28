"""Vehicle history queries are scoped view state, never account transactions."""
import copy
import types
import unittest
from unittest.mock import patch

from capture.history import reset_history_config
from capture.storage import read_json
import test_capture_runtime as harness
from capture.runtime import _view_request_id


class VehicleFilterRuntimeTests(unittest.TestCase):
    setUp = harness.RuntimeTests.setUp
    tearDown = harness.RuntimeTests.tearDown

    def request(self, identity=1, mode='all', vehicle='vehicle:321', context='NA:101'):
        return {'mode_key': mode, 'vehicle_key': vehicle,
                'request_id': identity, 'account_context': context}

    def capture(self):
        raw = harness.fixture()
        raw['common']['bonusType'] = 20
        with patch.object(self.collector, '_vehicle_item', return_value=None):
            self.events.onBattleResultsReceived.emit(True, raw)

    def test_vehicle_query_changes_only_memory_and_returns_matching_financial_history(self):
        self.capture()
        with patch.object(self.collector, '_vehicle_item', return_value=None):
            self.collector.panel_payload()
        config = copy.deepcopy(self.collector.config)
        ledger = read_json(self.collector.ledger_path)
        before_wallet = copy.deepcopy(self.collector.wallet.data)
        self.collector.set_vehicle_filter(self.request(mode='mode:20'))
        with patch.object(self.collector, '_vehicle_item', return_value=None):
            payload = self.collector.panel_payload()
        selection = payload['vehicle_selection']
        self.assertTrue(selection['available'])
        self.assertEqual(selection['request_id'], 1)
        self.assertEqual(selection['mode_key'], 'mode:20')
        self.assertEqual(selection['vehicle_key'], 'vehicle:321')
        self.assertEqual(selection['history_total'], 1)
        self.assertEqual(selection['summary']['net_credits'], 51500)
        self.assertEqual(payload['summary']['net_credits'], 51500)
        self.assertEqual(self.collector.config, config)
        self.assertEqual(read_json(self.collector.config_path), config)
        self.assertEqual(read_json(self.collector.ledger_path), ledger)
        self.assertEqual(self.collector.wallet.data, before_wallet)

    def test_wrong_account_bad_ids_types_and_paths_never_replace_valid_selection(self):
        self.collector.set_vehicle_filter(self.request())
        before = copy.deepcopy(self.collector._vehicle_filter)
        for changes in ({'account_context': 'NA:999'}, {'request_id': True}, {'request_id': 0},
                        {'request_id': 1.5}, {'request_id': 9007199254740992},
                        {'mode_key': 'mode:2147483648'}, {'mode_key': 'mode:01'},
                        {'mode_key': []}, {'vehicle_key': 'vehicle:0'},
                        {'vehicle_key': 'vehicle:2147483648'}, {'vehicle_key': '../../321'}):
            command = self.request(2)
            command.update(changes)
            self.collector.set_vehicle_filter(command)
            self.assertIsNotNone(self.collector.panel_error)
            self.assertEqual(self.collector._vehicle_filter, before)
        self.collector.set_vehicle_filter(None)
        self.assertEqual(self.collector._vehicle_filter, before)

    def test_out_of_order_commands_cannot_replace_latest_query_and_new_model_can_start_at_one(self):
        self.collector.panel.model = object()
        self.collector.set_vehicle_filter(self.request(2, vehicle='vehicle:654'))
        self.collector.set_vehicle_filter(self.request(1))
        self.assertEqual(self.collector._vehicle_filter['vehicle_key'], 'vehicle:654')
        self.assertEqual(self.collector._vehicle_filter['request_id'], 2)
        self.collector.panel.model = object()
        self.assertIsNone(self.collector.panel_payload()['vehicle_selection'])
        self.collector.set_vehicle_filter(self.request(1))
        self.assertEqual(self.collector._vehicle_filter['vehicle_key'], 'vehicle:321')
        self.assertEqual(self.collector._vehicle_filter['request_id'], 1)

    def test_account_and_history_generation_changes_drop_old_selection(self):
        self.collector.set_vehicle_filter(self.request())
        self.account = types.SimpleNamespace(databaseID=202, battleResultsCache=None)
        payload = self.collector.panel_payload()
        self.assertIsNone(payload['vehicle_selection'])
        self.assertIsNone(self.collector._vehicle_filter)
        self.account = types.SimpleNamespace(databaseID=101, battleResultsCache=None)
        self.collector.set_vehicle_filter(self.request(2))
        self.collector.config = reset_history_config(self.collector.config, 'NA', '101',
            22000000, '2026-10-19T12:00:00Z', [], [])
        self.assertIsNone(self.collector.panel_payload()['vehicle_selection'])
        self.assertIsNone(self.collector._vehicle_filter)

    def test_unknown_or_removed_vehicle_returns_explicit_empty_selection(self):
        self.capture()
        self.collector.set_vehicle_filter(self.request(vehicle='vehicle:999'))
        payload = self.collector.panel_payload()
        self.assertFalse(payload['vehicle_selection']['available'])
        self.assertEqual(payload['vehicle_selection']['history'], [])
        self.assertEqual(payload['vehicle_selection']['summary']['battle_count'], 0)
        self.assertEqual(payload['summary']['battle_count'], 1)

    def test_native_numeric_command_representations_return_numeric_response_ids(self):
        self.capture()
        for sequence, representation in ((1, '1'), (2, 2.0), (9007199254740991, '9007199254740991')):
            self.collector.set_vehicle_filter(self.request(representation, mode='mode:20'))
            self.assertIsNone(self.collector.panel_error)
            payload = self.collector.panel_payload()
            response = payload['vehicle_selection']
            self.assertEqual(response['request_id'], sequence)
            self.assertIsInstance(response['request_id'], int)
            self.assertEqual(response['summary']['net_credits'], 51500)

    def test_native_query_parser_rejects_lossy_and_ambiguous_sequence_representations(self):
        for value in (True, False, None, [], {}, 1.5, float('inf'), float('-inf'), float('nan'),
                      0, -1, 9007199254740992, 9007199254740992.0, '', '0', '-1', '+1',
                      '01', ' 1', '1 ', '1\n', '1.0', '1e2', '9007199254740992'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                _view_request_id(value)


if __name__ == '__main__':
    unittest.main()
