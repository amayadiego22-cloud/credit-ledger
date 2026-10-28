import copy
import types
import unittest
from capture.wallet import WalletBook, reward_receipt
from core import EconomyLedger

START = "2026-10-18T06:00:00Z"
AFTER = "2026-10-18T06:10:00Z"


def message(identity=1, data=None, sent=1792303800):
    return types.SimpleNamespace(messageId=identity, data=data or {}, sentTime=sent)


class WalletTests(unittest.TestCase):
    def setUp(self):
        self.wallet = WalletBook()
        self.ledger = EconomyLedger()
        self.wallet.observe("NA", "101", 22000000, START)

    def receipt(self, kind="tokenQuests", identity=1, battle=None, amount=150000):
        data = {"detailedRewards": {"crucible_1": {"credits": amount}}}
        if battle:
            data["arenaUniqueID"] = battle
        receipt = reward_receipt(message(identity, data), kind, AFTER,
                                 lambda q: "Crisol: etapa 1")
        receipt["occurred_at"] = AFTER
        return receipt

    def reconcile(self, balance):
        return self.wallet.reconciliation("NA", "101", self.ledger, balance)

    def test_repeated_receipt_and_restart_do_not_add_credits_twice(self):
        receipt = self.receipt()
        self.assertTrue(self.wallet.upsert_receipt("NA", "101", receipt))
        self.assertFalse(self.wallet.upsert_receipt("NA", "101", receipt))
        self.wallet = WalletBook(self.wallet.data)
        self.assertFalse(self.wallet.upsert_receipt("NA", "101", receipt))
        result = self.reconcile(22150000)
        self.assertEqual(result["external_credits"], 150000)
        self.assertEqual(result["unclassified"], 0)
        self.assertEqual(result["reconciled_balance"], 22150000)

    def test_battle_quest_is_annotation_and_never_extra_income(self):
        self.ledger.upsert_result({"region": "NA", "account_id": "101", "battle_id": "9001",
            "status": "final", "occurred_at": AFTER, "credits": {"gross": 200000,
            "expenses": {"repair": 10000, "ammo": 30000, "consumables": 10000, "other": 0}}})
        self.wallet.upsert_receipt("NA", "101", self.receipt("battleResults", battle=9001))
        result = self.reconcile(22150000)
        self.assertEqual(result["battle_net"], 150000)
        self.assertEqual(result["external_credits"], 0)
        self.assertEqual(result["unclassified"], 0)

    def test_same_explicit_battle_and_quest_link_is_not_a_second_award(self):
        self.wallet.upsert_receipt("NA", "101", self.receipt("battleResults", 1, 9001))
        self.wallet.upsert_receipt("NA", "101", self.receipt("tokenQuests", 2, 9001))
        self.assertEqual(self.reconcile(22000000)["external_credits"], 0)

    def test_late_receipt_reclassifies_unknown_change_without_changing_total(self):
        result = self.reconcile(22150000)
        self.assertEqual(result["unclassified"], 150000)
        self.wallet.upsert_receipt("NA", "101", self.receipt())
        result = self.reconcile(22150000)
        self.assertEqual(result["unclassified"], 0)
        self.assertEqual(result["change"], 150000)

    def test_correction_replaces_old_receipt_instead_of_adding_it(self):
        self.wallet.upsert_receipt("NA", "101", self.receipt(amount=150000))
        self.wallet.upsert_receipt("NA", "101", self.receipt(amount=180000))
        self.assertEqual(self.reconcile(22180000)["external_credits"], 180000)

    def test_movement_without_source_remains_unclassified_and_reconciles_exactly(self):
        result = self.reconcile(21950000)
        self.assertEqual(result["unclassified"], -50000)
        self.assertEqual(result["baseline"] + result["battle_net"] + result["external_credits"] + result["unclassified"], result["balance"])
        self.assertEqual(self.wallet.receipts("NA", "101"), [])

    def test_historical_receipts_are_part_of_base_not_new_earnings(self):
        receipt = self.receipt()
        receipt["occurred_at"] = "2026-10-17T06:00:00Z"
        self.wallet.upsert_receipt("NA", "101", receipt)
        self.assertEqual(self.reconcile(22000000)["external_credits"], 0)

    def test_accounts_and_real_zero_balance_are_separate(self):
        self.wallet.observe("NA", "102", 0, START)
        self.wallet.upsert_receipt("NA", "102", self.receipt())
        self.assertEqual(self.reconcile(22000000)["external_credits"], 0)
        other = self.wallet.reconciliation("NA", "102", self.ledger, 150000)
        self.assertEqual(other["baseline"], 0)
        self.assertEqual(other["external_credits"], 150000)
        self.assertFalse(self.wallet.reconciliation("EU", "102", self.ledger, None)["ready"])

    def test_only_actual_integer_credit_rewards_are_read(self):
        for amount in (True, "150000", 150000.5, None):
            self.assertIsNone(reward_receipt(message(data={"detailedRewards": {"q": {"credits": amount}}}), "tokenQuests", AFTER))
        self.assertIsNone(reward_receipt(message(identity=None, data={"credits": 10}), "tokenQuests", AFTER))
        self.assertIsNone(reward_receipt(message(data={"credits": 10}), "unknown", AFTER))
        reward = reward_receipt(message(data={"credits": 150000,
             "detailedRewards": {"q": {"credits": 150000}}}), "tokenQuests", AFTER)
        self.assertEqual(reward["credits"], 150000)
        self.assertFalse(reward["parts"][0]["name_resolved"])

    def test_invoice_amount_must_be_explicitly_verified_by_adapter(self):
        msg = message(data={"data": {"credits": 60000}})
        self.assertIsNone(reward_receipt(msg, "invoiceReceived", AFTER))
        receipt = reward_receipt(msg, "invoiceReceived", AFTER, invoice_amount=-60000)
        self.assertEqual(receipt["credits"], -60000)

    def test_observation_does_not_reset_base_and_invalid_balance_is_not_zero(self):
        self.assertFalse(self.wallet.observe("NA", "101", True, AFTER))
        self.wallet.observe("NA", "101", 23000000, AFTER)
        self.assertEqual(self.reconcile(23000000)["baseline"], 22000000)
        self.assertEqual(self.reconcile(23000000)["change"], 1000000)
        self.assertFalse(self.wallet.reconciliation("NA", "101", self.ledger, None)["ready"])


if __name__ == "__main__":
    unittest.main()
