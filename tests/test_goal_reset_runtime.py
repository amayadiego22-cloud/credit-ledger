"""An explicit goal restart commits only goal configuration, atomically."""
import copy
import unittest
from unittest.mock import patch

from capture import runtime
from capture.storage import atomic_json, read_json
import test_capture_runtime as harness


START = '2026-10-18T12:00:00Z'
RESTART = '2026-10-18T13:00:00Z'
BASE = 22000000
KEY = 'NA:101'


class GoalResetRuntimeTests(unittest.TestCase):
    setUp = harness.RuntimeTests.setUp
    tearDown = harness.RuntimeTests.tearDown

    def started_goal(self):
        self.balance = BASE
        with patch.object(runtime, '_now_utc', return_value=START):
            self.collector.save_goal({'value': '1000000', 'mode': 'balance_growth'})
        return copy.deepcopy(self.collector.config['account_goals'][KEY])

    def reset(self, value='2000000'):
        with patch.object(runtime, '_now_utc', return_value=RESTART):
            self.collector.reset_goal({'value': value, 'mode': 'balance_growth'})

    def test_explicit_reset_keeps_history_wallet_other_account_and_financial_files(self):
        self.started_goal()
        self.events.onBattleResultsReceived.emit(True, harness.fixture())
        self.balance = BASE + 51500
        self.collector._sync_finance()
        self.collector.config['account_history'] = {KEY: {'mode': 'manual', 'hour': 6,
            'preserve_goal': False, 'since_utc': None, 'baseline': BASE,
            'generation': 7, 'excluded_battles': [], 'excluded_receipts': [],
            'daily_cycle': None, 'clock': 'local_v1'}}
        self.collector.config['account_goals']['NA:202'] = {
            'schema': 2, 'mode': 'balance_growth', 'target': 9000000,
            'baseline': 41000000, 'since_utc': START}
        atomic_json(self.collector.config_path, self.collector.config)
        before = copy.deepcopy(self.collector.config)
        before_ledger = read_json(self.collector.ledger_path)
        before_wallet = read_json(self.collector.wallet_path)
        self.reset()
        self.assertIsNone(self.collector.panel_error)
        saved = read_json(self.collector.config_path)
        goal = saved['account_goals'][KEY]
        self.assertEqual((goal['target'], goal['baseline'], goal['since_utc']),
                         (2000000, BASE + 51500, RESTART))
        self.assertEqual(goal['reset_generation'], 1)
        self.assertEqual(saved['account_goals']['NA:202'], before['account_goals']['NA:202'])
        self.assertEqual(saved['account_history'], before['account_history'])
        self.assertEqual(read_json(self.collector.ledger_path), before_ledger)
        self.assertEqual(read_json(self.collector.wallet_path), before_wallet)
        payload = self.collector.panel_payload()
        self.assertEqual(payload['goal']['reset_generation'], 1)
        self.assertEqual(payload['goal']['current'], 0)
        self.assertEqual(payload['goal']['progress_percent'], 0)
        self.assertEqual(payload['summary']['battle_count'], 1)
        self.assertEqual(payload['summary']['net_credits'], 51500)

    def test_failed_reset_commit_keeps_goal_and_generation_on_disk_and_in_memory(self):
        self.started_goal()
        before = copy.deepcopy(self.collector.config)
        self.balance = BASE + 123456
        with patch.object(runtime, 'atomic_json', side_effect=OSError('synthetic write failure')), \
                patch.object(self.collector, '_error') as error, \
                patch.object(self.collector.panel, 'refresh') as refreshed:
            self.reset()
        error.assert_called_once_with('goal_reset_failed')
        self.assertIsNotNone(self.collector.panel_error)
        self.assertEqual(self.collector.config, before)
        self.assertEqual(read_json(self.collector.config_path), before)
        refreshed.assert_called_with(force=True)

    def test_unknown_balance_zero_and_bad_request_do_not_change_saved_goal(self):
        self.started_goal()
        before = copy.deepcopy(self.collector.config)
        self.balance = None
        self.reset()
        self.assertIsNotNone(self.collector.panel_error)
        self.assertEqual(self.collector.config, before)
        self.balance = BASE + 100000
        self.reset('0')
        self.assertIsNotNone(self.collector.panel_error)
        self.assertEqual(self.collector.config, before)
        for request in (None, [], {'value': '1', 'mode': 'balance'}):
            self.collector.reset_goal(request)
            self.assertIsNotNone(self.collector.panel_error)
            self.assertEqual(self.collector.config, before)
        self.account = None
        self.reset()
        self.assertIsNotNone(self.collector.panel_error)
        self.assertEqual(read_json(self.collector.config_path), before)

    def test_reset_generation_survives_collector_restart_and_regular_disable_resume(self):
        self.started_goal()
        self.balance = BASE + 51500
        self.reset()
        reset_goal = copy.deepcopy(self.collector.config['account_goals'][KEY])
        self.collector.close()
        reopened = runtime.Collector()
        try:
            with patch.object(reopened, '_read_balance', return_value=BASE + 76500):
                reopened.save_goal({'value': '0', 'mode': 'balance_growth'})
                reopened.save_goal({'value': '3000000', 'mode': 'balance_growth'})
                payload = reopened.panel_payload()
            self.assertEqual(payload['goal']['reset_generation'], 1)
            self.assertEqual(payload['goal']['baseline'], reset_goal['baseline'])
            self.assertEqual(payload['goal']['since_utc'], reset_goal['since_utc'])
            self.assertEqual(payload['goal']['current'], 25000)
        finally:
            reopened.close()


if __name__ == '__main__':
    unittest.main()
