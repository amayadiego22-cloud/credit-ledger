"""Reserve components follow the actual effective aggregate, without new income."""
import copy
import unittest
from unittest.mock import patch

from capture import runtime
from capture.native import derive_credits
from capture.snapshot import make_snapshot
from capture.normalizer import normalize_snapshot
from test_native_finance import Personal, Records, Reusable
from test_snapshot import fixture
import test_capture_runtime as runtime_tests


class ReserveRows(Personal):
    def getMoneyRecords(self):
        return iter([
            (Records(credits=80000, originalCreditsToDraw=500,
                     boosterCredits=10000, boosterCreditsFactor100=5000,
                     orderCreditsFactor100=8000),
             Records(credits=120000, originalCreditsToDraw=500,
                     boosterCredits=15000, boosterCreditsFactor100=7500,
                     orderCreditsFactor100=12000),
             Records(), Records(autoRepairCost=-8000, autoLoadCredits=-12000,
                                autoEquipCredits=-9000),
             Records(credits=999999, boosterCredits=888888),
             Records(credits=999999, orderCreditsFactor100=888888)),
            # Native iterators contain per-vehicle rows after the aggregate.
            (Records(credits=80000, boosterCredits=9000), Records(), Records(),
             Records(), Records(), Records())])


class NativeReserveTests(unittest.TestCase):
    def derive(self, personal=None):
        return derive_credits(fixture(), lambda _: Reusable(personal or ReserveRows()))

    def test_two_personal_record_names_are_summed_and_clan_separated(self):
        value = self.derive()
        self.assertEqual(value['reserves'], {'personal': 15000, 'clan': 8000})
        self.assertEqual(value['totals']['gross'], 80500)
        self.assertEqual(value['totals']['net'], 51500)
        self.assertEqual(len(value['rows']), 1)

    def test_effective_premium_column_excludes_wot_plus_preview_and_vehicle_rows(self):
        personal = ReserveRows()
        personal.hasAnyPremium = True
        personal.isWotPlus = True
        value = self.derive(personal)
        self.assertEqual(value['reserves'], {'personal': 22500, 'clan': 12000})
        self.assertEqual(value['totals']['gross'], 120500)
        self.assertEqual(value['totals']['net'], 91500)

    def test_absent_replay_entries_are_known_zero_on_valid_native_records(self):
        self.assertEqual(self.derive(Personal())['reserves'], {'personal': 0, 'clan': 0})

    def test_optional_invalid_reserves_do_not_drop_verified_battle_income(self):
        for personal_bonus, clan_bonus in ((1.5, 0), (float('nan'), 0),
                                           (-1, 0), (0, -1), (50000, 50000)):
            class InvalidRows(Personal):
                def getMoneyRecords(self):
                    rows = list(Personal.getMoneyRecords(self))
                    rows[0][0].values.update(boosterCredits=personal_bonus,
                                            orderCreditsFactor100=clan_bonus)
                    return iter(rows)
            value = self.derive(InvalidRows())
            self.assertNotIn('reserves', value)
            self.assertEqual(value['totals']['net'], 51500)
            self.assertEqual(value['reserves_error'], 'NativeFinanceError')

    def test_boolean_or_unavailable_native_query_stays_unknown(self):
        for returned in (True, None):
            class UnavailableRecords(Records):
                def getRecord(self, *names):
                    if 'boosterCredits' in names:
                        return returned
                    return Records.getRecord(self, *names)
            class UnavailableRows(Personal):
                def getMoneyRecords(self):
                    rows = list(Personal.getMoneyRecords(self))
                    row = list(rows[0])
                    row[0] = UnavailableRecords(**row[0].values)
                    return iter([row])
            value = self.derive(UnavailableRows())
            self.assertNotIn('reserves', value)
            self.assertEqual(value['totals']['gross'], 80500)

    def test_normalized_snapshot_keeps_reserves_and_exact_financial_amounts(self):
        snapshot = make_snapshot(fixture(), 'NA')
        snapshot['native_credits'] = self.derive()
        before = copy.deepcopy(snapshot)
        record = normalize_snapshot(snapshot)
        self.assertEqual(record['credits']['reserves'], {'personal': 15000, 'clan': 8000})
        self.assertEqual(record['credits']['gross'], 80500)
        self.assertEqual(sum(record['credits']['expenses'].values()), 29000)
        self.assertEqual(snapshot, before)


class RuntimeReserveTests(unittest.TestCase):
    setUp = runtime_tests.RuntimeTests.setUp
    tearDown = runtime_tests.RuntimeTests.tearDown

    def test_event_capture_restart_and_duplicate_results_keep_one_bonus_aggregate(self):
        self.balance = 22051500
        with patch.object(runtime, 'derive_credits',
                          side_effect=lambda result: derive_credits(result, lambda _: Reusable(ReserveRows()))):
            self.events.onBattleResultsReceived.emit(True, fixture())
            self.events.onBattleResultsReceived.emit(True, fixture())
        payload = self.collector.panel_payload()
        self.assertEqual(payload['summary']['battle_count'], 1)
        self.assertEqual(payload['summary']['gross_credits'], 80500)
        self.assertEqual(payload['summary']['net_credits'], 51500)
        self.assertEqual(payload['summary']['reserves'],
                         {'personal': 15000, 'clan': 8000, 'known_battles': 1, 'total_battles': 1})
        self.assertEqual(payload['history'][0]['reserves'], {'personal': 15000, 'clan': 8000})
        restored = type(self.collector.ledger).load(self.collector.ledger_path)
        self.assertEqual(restored.summary('NA', '101')['net_credits'], 51500)
        self.assertEqual(restored.list_results()[0]['credits']['reserves'],
                         {'personal': 15000, 'clan': 8000})


if __name__ == '__main__':
    unittest.main()
