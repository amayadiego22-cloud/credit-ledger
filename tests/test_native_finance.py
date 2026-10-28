import copy
import unittest

from capture.native import NativeFinanceError, derive_credits, _integer
from capture.normalizer import ReconciliationError, normalize_snapshot
from capture.snapshot import make_snapshot
from core import EconomyLedger
from test_snapshot import fixture


class Records(object):
    def __init__(self, **values):
        self.values = values

    def getRecord(self, *names):
        return sum(self.values.get(name, 0) for name in names)


class Personal(object):
    hasAnyPremium = False
    isWotPlus = False

    def getMoneyRecords(self):
        return iter([(Records(credits=80000, originalCreditsToDraw=500),
                      Records(credits=120000, originalCreditsToDraw=500),
                      Records(), Records(autoRepairCost=-8000, autoLoadCredits=-12000,
                                         autoEquipCredits=-9000),
                      Records(credits=999999), Records(credits=999999))])


class Reusable(object):
    def __init__(self, personal=None):
        self.personal = personal or Personal()


class NativeFinanceTests(unittest.TestCase):
    def test_native_integral_floats_are_exact_credit_amounts(self):
        for observed in (21696.0, 33996.0, -75900.0, 0.0):
            self.assertEqual(_integer(observed, "observed"), int(observed))
        for observed in (1.5, float("nan"), float("inf"), 9007199254740992.0, True):
            with self.assertRaises(NativeFinanceError):
                _integer(observed, "observed")

    def test_float_native_records_use_exact_values_without_rounding(self):
        class FloatRows(Personal):
            def getMoneyRecords(self):
                return iter([(Records(credits=21696.0), Records(credits=21696.0),
                              Records(), Records(autoRepairCost=-33996.0,
                                                 autoLoadCredits=-33600.0,
                                                 autoEquipCredits=-30000.0),
                              Records(), Records())])
        native = derive_credits(fixture(), lambda result: Reusable(FloatRows()))
        self.assertEqual(native["totals"]["net"], -75900)
    def test_base_uses_native_bonus_and_expenses_once(self):
        native = derive_credits(fixture(), lambda result: Reusable())
        self.assertEqual(native["totals"]["gross"], 80500)
        self.assertEqual(native["totals"]["net"], 51500)

    def test_aggregate_followed_by_vehicle_rows_is_not_double_counted(self):
        class MultipleRows(Personal):
            def getMoneyRecords(self):
                row = list(Personal.getMoneyRecords(self))[0]
                return iter([row, row])
        native = derive_credits(fixture(), lambda result: Reusable(MultipleRows()))
        self.assertEqual(native["totals"]["gross"], 80500)
        self.assertEqual(native["totals"]["net"], 51500)
        self.assertEqual(len(native["rows"]), 1)

    def test_premium_uses_effective_column_not_wot_plus_preview(self):
        personal = Personal()
        personal.hasAnyPremium = True
        personal.isWotPlus = True
        native = derive_credits(fixture(), lambda result: Reusable(personal))
        self.assertEqual(native["totals"]["gross"], 120500)
        self.assertEqual(native["totals"]["net"], 91500)
        self.assertTrue(native["is_wot_plus"])

    def test_positive_native_expense_is_not_silently_negated(self):
        class Unexpected(Personal):
            def getMoneyRecords(self):
                return iter([(Records(credits=100), Records(), Records(),
                              Records(autoRepairCost=5), Records(), Records())])
        with self.assertRaises(NativeFinanceError):
            derive_credits(fixture(), lambda result: Reusable(Unexpected()))

    def test_no_native_data_is_not_counted_as_zero_income(self):
        with self.assertRaises(ReconciliationError):
            normalize_snapshot(make_snapshot(fixture(), "NA"))

    def test_native_rows_normalize_and_enter_ledger(self):
        snapshot = make_snapshot(fixture(), "NA")
        snapshot["native_credits"] = derive_credits(fixture(), lambda result: Reusable())
        record = normalize_snapshot(snapshot)
        ledger = EconomyLedger()
        ledger.upsert_result(record)
        self.assertEqual(ledger.summary("NA", "101")["net_credits"], 51500)
        changed = copy.deepcopy(snapshot)
        changed["native_credits"]["totals"]["net"] += 1
        with self.assertRaises(ReconciliationError):
            normalize_snapshot(changed)

    def test_missing_or_invalid_replay_is_not_zero_income(self):
        for replay in [None, b"", b"\x01\x00", b"not-a-replay"]:
            result = fixture()
            result["personal"][321]["creditsReplay"] = replay
            with self.assertRaises(NativeFinanceError):
                derive_credits(result, lambda result: Reusable())


if __name__ == "__main__":
    unittest.main()
