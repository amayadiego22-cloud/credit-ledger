# -*- coding: utf-8 -*-
from __future__ import division

import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import EconomyLedger, LedgerValidationError
from core import ledger as ledger_module


def result(battle="battle-1", gross=100000, repair=10000, ammo=20000,
           consumables=5000, other=0, account="123", region="NA",
           occurred_at="2026-10-17T15:00:00Z", status="final", resources=None):
    value = {
        "region": region,
        "account_id": account,
        "battle_id": battle,
        "occurred_at": occurred_at,
        "status": status,
        "credits": {
            "gross": gross,
            "expenses": {"repair": repair, "ammo": ammo,
                         "consumables": consumables, "other": other},
        },
    }
    if resources is not None:
        value["resources"] = resources
    return value


def goal(mode="net_earnings", target=200000, resource="credits",
         since="2026-10-17T00:00:00Z", account="123", region="NA"):
    return {"region": region, "account_id": account, "mode": mode,
            "target": target, "resource": resource, "since_utc": since}


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.ledger = EconomyLedger()

    def test_duplicate_identity_is_idempotent(self):
        self.assertEqual("inserted", self.ledger.upsert_result(result()))
        self.assertEqual("unchanged", self.ledger.upsert_result(result()))
        totals = self.ledger.summary("NA", 123)
        self.assertEqual(1, totals["battle_count"])
        self.assertEqual(65000, totals["net_credits"])
        self.assertEqual(35000, totals["total_expenses"])

    def test_losses_remain_negative_and_expenses_are_deducted_once(self):
        self.ledger.upsert_result(result(gross=15000, repair=10000, ammo=10000,
                                         consumables=5000, other=1000))
        totals = self.ledger.summary("NA", "123")
        self.assertEqual(26000, totals["total_expenses"])
        self.assertEqual(-11000, totals["net_credits"])
        self.assertEqual(-11000, totals["average_net_credits"])

    def test_corrected_result_replaces_amounts_without_new_battle(self):
        self.ledger.upsert_result(result())
        corrected = result(gross=150000, repair=5000)
        self.assertEqual("updated", self.ledger.upsert_result(corrected))
        totals = self.ledger.summary("NA", "123")
        self.assertEqual(1, totals["battle_count"])
        self.assertEqual(150000, totals["gross_credits"])
        self.assertEqual(120000, totals["net_credits"])

    def test_same_battle_id_is_isolated_by_account_and_region(self):
        self.ledger.upsert_result(result(account="123", region="NA"))
        self.ledger.upsert_result(result(account="456", region="NA", gross=200000))
        self.ledger.upsert_result(result(account="123", region="EU", gross=300000))
        self.assertEqual(65000, self.ledger.summary("NA", "123")["net_credits"])
        self.assertEqual(165000, self.ledger.summary("NA", "456")["net_credits"])
        self.assertEqual(265000, self.ledger.summary("EU", "123")["net_credits"])
        self.assertEqual(0, self.ledger.summary("ASIA", "123")["battle_count"])

    def test_pending_is_excluded_until_complete_final_arrives(self):
        pending = result(status="pending")
        del pending["credits"]
        self.ledger.upsert_result(pending)
        totals = self.ledger.summary("NA", "123")
        self.assertEqual(0, totals["battle_count"])
        self.assertEqual(1, totals["pending_battles"])
        self.assertEqual(0, totals["net_credits"])
        self.assertIsNone(totals["average_net_credits"])
        self.assertIsNone(self.ledger.goal_status(goal())["estimated_battles"])
        self.assertEqual("updated", self.ledger.upsert_result(result()))
        totals = self.ledger.summary("NA", "123")
        self.assertEqual(1, totals["battle_count"])
        self.assertEqual(0, totals["pending_battles"])
        self.assertEqual(65000, totals["net_credits"])

    def test_pending_with_amounts_still_does_not_contribute(self):
        self.ledger.upsert_result(result(status="pending", gross=999999))
        self.assertEqual(0, self.ledger.summary("NA", "123")["gross_credits"])

    def test_late_pending_notification_cannot_downgrade_final(self):
        self.ledger.upsert_result(result())
        self.assertEqual("ignored_pending", self.ledger.upsert_result(result(status="pending")))
        totals = self.ledger.summary("NA", "123")
        self.assertEqual(1, totals["battle_count"])
        self.assertEqual(0, totals["pending_battles"])
        self.assertEqual(65000, totals["net_credits"])
        self.assertEqual("updated", self.ledger.upsert_result(result(gross=150000)))
        self.assertEqual(115000, self.ledger.summary("NA", "123")["net_credits"])

    def test_net_goal_uses_inclusive_utc_cutoff(self):
        self.ledger.upsert_result(result(battle="old", gross=900000,
                                         occurred_at="2026-10-16T23:59:59Z"))
        self.ledger.upsert_result(result(battle="boundary", gross=100000,
                                         occurred_at="2026-10-17T00:00:00Z"))
        status = self.ledger.goal_status(goal(target=130000))
        self.assertEqual(65000, status["current"])
        self.assertEqual(65000, status["remaining"])
        self.assertEqual(50, status["progress_percent"])
        self.assertEqual(1, status["battle_count"])
        self.assertEqual(1, status["estimated_battles"])

    def test_achieved_goal_clamps_progress_and_needs_zero_battles(self):
        self.ledger.upsert_result(result())
        status = self.ledger.goal_status(goal(target=50000))
        self.assertTrue(status["complete"])
        self.assertEqual(100, status["progress_percent"])
        self.assertEqual(0, status["remaining"])
        self.assertEqual(0, status["estimated_battles"])

    def test_positive_average_estimate_rounds_up(self):
        self.ledger.upsert_result(result())
        status = self.ledger.goal_status(goal(target=200000))
        self.assertEqual(3, status["estimated_battles"])

    def test_zero_or_negative_average_never_predicts_recovery(self):
        for gross, expected in ((35000, 0), (25000, -10000)):
            self.ledger = EconomyLedger()
            self.ledger.upsert_result(result(gross=gross))
            status = self.ledger.goal_status(goal())
            self.assertEqual(expected, status["average_per_battle"])
            self.assertIsNone(status["estimated_battles"])
            self.assertEqual(0, status["progress_percent"])
            self.assertEqual(200000 - expected, status["remaining"])

    def test_balance_goal_requires_external_real_balance(self):
        self.ledger.upsert_result(result())
        with self.assertRaises(LedgerValidationError):
            self.ledger.goal_status(goal(mode="balance"))
        status = self.ledger.goal_status(goal(mode="balance", target=500000),
                                         external_balance=435000)
        self.assertEqual(435000, status["current"])
        self.assertEqual(65000, status["remaining"])
        self.assertEqual(1, status["estimated_battles"])

    def test_other_resource_uses_net_amount_and_all_final_battles(self):
        self.ledger.upsert_result(result(resources={"bonds": {"earned": 30, "spent": 5}}))
        self.ledger.upsert_result(result(battle="battle-2"))
        totals = self.ledger.summary("NA", "123")["resources"]["bonds"]
        self.assertEqual(25, totals["net"])
        self.assertEqual(12.5, totals["average_net"])
        status = self.ledger.goal_status(goal(resource="bonds", target=50))
        self.assertEqual(25, status["current"])
        self.assertEqual(2, status["estimated_battles"])

    def test_record_inputs_and_returns_are_defensive_copies(self):
        incoming = result()
        self.ledger.upsert_result(incoming)
        incoming["credits"]["gross"] = 0
        outgoing = self.ledger.list_results()
        outgoing[0]["credits"]["gross"] = 1
        self.assertEqual(100000, self.ledger.summary("NA", "123")["gross_credits"])

    def test_money_rejects_bool_negative_float_and_string(self):
        for invalid in (True, False, -1, 1.5, "100"):
            for field in ("gross", "repair"):
                incoming = result()
                if field == "gross":
                    incoming["credits"]["gross"] = invalid
                else:
                    incoming["credits"]["expenses"]["repair"] = invalid
                with self.assertRaises(LedgerValidationError):
                    self.ledger.upsert_result(incoming)
        self.assertEqual([], self.ledger.list_results())

    def test_rejects_ambiguous_subtotals_missing_expenses_and_incomplete_final(self):
        invalid = []
        incoming = result()
        incoming["credits"]["net"] = 65000
        invalid.append(incoming)
        incoming = result()
        del incoming["credits"]["expenses"]["ammo"]
        invalid.append(incoming)
        incoming = result()
        del incoming["credits"]
        invalid.append(incoming)
        for incoming in invalid:
            with self.assertRaises(LedgerValidationError):
                self.ledger.upsert_result(incoming)

    def test_rejects_non_utc_cutoff_and_missing_net_goal_start(self):
        for value in ("2026-10-17", "2026-10-17T00:00:00-05:00",
                      "2026-10-17T00:00:00", "2026-02-30T00:00:00Z"):
            with self.assertRaises(LedgerValidationError):
                self.ledger.goal_status(goal(since=value))
        with self.assertRaises(LedgerValidationError):
            self.ledger.goal_status(goal(since=None))

    def test_unknown_resource_without_gains_does_not_predict(self):
        self.ledger.upsert_result(result())
        status = self.ledger.goal_status(goal(resource="gold", target=100))
        self.assertEqual(0, status["current"])
        self.assertIsNone(status["estimated_battles"])

    def test_corrupt_document_and_duplicate_persisted_keys_are_rejected(self):
        self.ledger.upsert_result(result())
        duplicate = self.ledger.to_dict()
        duplicate["records"].append(copy.deepcopy(duplicate["records"][0]))
        with self.assertRaises(LedgerValidationError):
            EconomyLedger.from_dict(duplicate)
        with self.assertRaises(LedgerValidationError):
            EconomyLedger.from_dict({"schema_version": 999, "records": []})


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="wot-ledger-test-")
        self.path = os.path.join(self.directory, "ledger.json")

    def tearDown(self):
        shutil.rmtree(self.directory)

    def test_round_trip_and_replacing_existing_file(self):
        original = EconomyLedger()
        original.upsert_result(result(resources={"bonds": {"earned": 10, "spent": 3}}))
        original.upsert_result(result(battle="pending", status="pending"))
        original.save(self.path)
        loaded = EconomyLedger.load(self.path)
        self.assertEqual(original.to_dict(), loaded.to_dict())
        self.assertEqual(original.summary("NA", "123"), loaded.summary("NA", "123"))
        loaded.upsert_result(result(gross=200000))
        loaded.save(self.path)
        again = EconomyLedger.load(self.path)
        self.assertEqual(165000, again.summary("NA", "123")["net_credits"])
        self.assertEqual(2, len(again.list_results()))

    def test_replace_failure_retains_prior_bytes_and_removes_temporary(self):
        previous = EconomyLedger()
        previous.upsert_result(result())
        previous.save(self.path)
        with open(self.path, "rb") as handle:
            before = handle.read()
        previous.upsert_result(result(gross=200000))
        real_replace = ledger_module._atomic_replace

        def fail_replace(source, destination):
            raise OSError("simulated locked destination")

        ledger_module._atomic_replace = fail_replace
        try:
            with self.assertRaises(OSError):
                previous.save(self.path)
        finally:
            ledger_module._atomic_replace = real_replace
        with open(self.path, "rb") as handle:
            self.assertEqual(before, handle.read())
        self.assertEqual(["ledger.json"], os.listdir(self.directory))
        self.assertEqual(65000, EconomyLedger.load(self.path).summary("NA", "123")["net_credits"])

    def test_fsync_failure_retains_prior_bytes_and_removes_temporary(self):
        ledger = EconomyLedger()
        ledger.upsert_result(result())
        ledger.save(self.path)
        with open(self.path, "rb") as handle:
            before = handle.read()
        ledger.upsert_result(result(gross=200000))
        real_fsync = ledger_module.os.fsync

        def fail_fsync(descriptor):
            raise OSError("simulated storage failure")

        ledger_module.os.fsync = fail_fsync
        try:
            with self.assertRaises(OSError):
                ledger.save(self.path)
        finally:
            ledger_module.os.fsync = real_fsync
        with open(self.path, "rb") as handle:
            self.assertEqual(before, handle.read())
        self.assertEqual(["ledger.json"], os.listdir(self.directory))


if __name__ == "__main__":
    unittest.main()
