"""Previous-day queries remain bounded, account-scoped, read-only view state."""
import calendar
import copy
import datetime
import types
import unittest
from unittest.mock import patch

from capture.history import reset_history_config
from capture.server_clock import server_day_clock
from capture.storage import read_json
import test_capture_runtime as harness


DAY = '2026-10-18T10:00:00Z'
NOW = '2026-10-19T12:00:00Z'


class ArchiveRuntimeTests(unittest.TestCase):
    tearDown = harness.RuntimeTests.tearDown

    def setUp(self):
        harness.RuntimeTests.setUp(self)
        parsed = datetime.datetime.strptime(NOW, '%Y-%m-%dT%H:%M:%SZ')
        clock = server_day_clock(calendar.timegm(parsed.timetuple()), 36000)
        self.native = patch.object(self.collector, '_read_server_clock', return_value=clock)
        self.native.start()
        self.addCleanup(self.native.stop)
        self.balance = 22000000
        self.collector.panel_payload()

    def request(self, sequence=1, day=DAY, mode='all', vehicle='all', context='NA:101'):
        return {'day_key': day, 'mode_key': mode, 'vehicle_key': vehicle,
                'request_id': sequence, 'account_context': context}

    def capture_old(self):
        raw = harness.fixture()
        stamp = datetime.datetime.strptime('2026-10-18T12:00:00Z', '%Y-%m-%dT%H:%M:%SZ')
        raw['common'].update(arenaCreateTime=calendar.timegm(stamp.timetuple()) - 300,
                             duration=300, bonusType=20)
        with patch.object(self.collector, '_vehicle_item', return_value=None):
            self.events.onBattleResultsReceived.emit(True, raw)
            self.collector.panel_payload()

    def test_prior_day_query_returns_full_scoped_finance_without_mutating_live_period(self):
        self.capture_old()
        before = self.collector.panel_payload()
        config = read_json(self.collector.config_path)
        ledger = read_json(self.collector.ledger_path)
        wallet = copy.deepcopy(self.collector.wallet.data)
        self.collector.set_archive_selection(self.request('1', mode='mode:20', vehicle='vehicle:321'))
        payload = self.collector.panel_payload()
        selected = payload['history_archive']['selection']
        self.assertTrue(selected['available'])
        self.assertEqual(selected['request_id'], 1)
        self.assertEqual(selected['day_key'], DAY)
        self.assertEqual(selected['history_total'], 1)
        self.assertEqual(selected['summary']['net_credits'], 51500)
        self.assertEqual(len(selected['history']), 1)
        for key in ('summary', 'goal', 'balance', 'wallet', 'history_control'):
            self.assertEqual(payload[key], before[key])
        self.assertEqual(read_json(self.collector.config_path), config)
        self.assertEqual(read_json(self.collector.ledger_path), ledger)
        self.assertEqual(self.collector.wallet.data, wallet)

    def test_invalid_accounts_dates_keys_and_sequence_ids_preserve_valid_query(self):
        self.collector.set_archive_selection(self.request())
        before = copy.deepcopy(self.collector._archive_filter)
        for changes in ({'account_context': 'NA:202'}, {'day_key': '../ledger.json'},
                        {'day_key': '2026-10-32T10:00:00Z'}, {'day_key': '2026-1-18T10:00:00Z'},
                        {'day_key': ['2026-10-18T10:00:00Z']}, {'mode_key': 'mode:01'},
                        {'vehicle_key': 'vehicle:0'}, {'request_id': True}, {'request_id': '1.0'}):
            query = self.request(2)
            query.update(changes)
            self.collector.set_archive_selection(query)
            self.assertIsNotNone(self.collector.panel_error)
            self.assertEqual(self.collector._archive_filter, before)

    def test_stale_queries_are_ignored_and_new_model_can_restart_sequence(self):
        self.collector.panel.model = object()
        self.collector.set_archive_selection(self.request('2', mode='mode:20'))
        self.collector.set_archive_selection(self.request(1.0))
        self.assertEqual(self.collector._archive_filter['mode_key'], 'mode:20')
        self.assertEqual(self.collector._archive_filter['request_id'], 2)
        self.collector.panel.model = object()
        self.assertIsNone(self.collector.panel_payload()['history_archive']['selection'])
        self.collector.set_archive_selection(self.request(1.0))
        self.assertEqual(self.collector._archive_filter['request_id'], 1)

    def test_account_and_visible_history_resets_drop_archive_selection(self):
        self.collector.set_archive_selection(self.request())
        self.account = types.SimpleNamespace(databaseID=202, battleResultsCache=None)
        self.assertIsNone(self.collector.panel_payload()['history_archive']['selection'])
        self.account = types.SimpleNamespace(databaseID=101, battleResultsCache=None)
        self.collector.set_archive_selection(self.request(2))
        self.collector.config = reset_history_config(self.collector.config, 'NA', '101',
            self.balance, NOW, [], [], clear_goal=True)
        self.assertIsNone(self.collector.panel_payload()['history_archive']['selection'])

    def test_nonexistent_day_has_explicit_empty_response_instead_of_waiting_forever(self):
        self.collector.set_archive_selection(self.request(day='2026-10-17T10:00:00Z'))
        selection = self.collector.panel_payload()['history_archive']['selection']
        self.assertEqual(selection['request_id'], 1)
        self.assertFalse(selection['available'])
        self.assertEqual(selection['summary']['battle_count'], 0)
        self.assertEqual(selection['history'], [])

    def test_only_queried_older_day_refreshes_tank_art_and_leaves_financial_evidence_intact(self):
        from test_mode_filters import result
        event_icon = 'coui://halloween/gui/maps/icons/vehicle/usa-A100_T49_Halloween_event.extend.png'
        for identity, occurred_at, vehicle_type in (
                (1, '2026-10-18T12:00:00Z', '321'),
                (2, '2026-10-17T12:00:00Z', '654')):
            record = result(identity, 102)
            record['occurred_at'] = occurred_at
            record['vehicles'] = [{'vehicle_type_id': vehicle_type,
                                   'name': 'Vehículo ' + vehicle_type, 'tier': None, 'icon': None}]
            self.collector.ledger.upsert_result(record)
        self.collector.config = reset_history_config(self.collector.config, 'NA', '101',
            self.balance, NOW, [], [], clear_goal=True)
        before = self.collector.ledger.to_dict()
        self.collector.set_archive_selection(self.request())
        native = types.SimpleNamespace(userName='Granadero', level=9, icon=event_icon)
        with patch.object(self.collector, '_vehicle_item', return_value=native) as getter:
            selected = self.collector.panel_payload()['history_archive']['selection']
        getter.assert_called_once_with(321)
        self.assertEqual(selected['history'][0]['vehicles'][0]['icon'], event_icon)
        self.assertEqual(selected['history'][0]['vehicles'][0]['tier'], 9)
        after = self.collector.ledger.to_dict()
        for old, new in zip(before['records'], after['records']):
            old_vehicles, new_vehicles = old.pop('vehicles'), new.pop('vehicles')
            self.assertEqual(old, new)
            if old_vehicles[0]['vehicle_type_id'] == '654':
                self.assertEqual(old_vehicles, new_vehicles)


if __name__ == '__main__':
    unittest.main()
