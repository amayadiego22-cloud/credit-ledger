"""Completion event lifecycle independently of UI renders or financial storage."""
import copy
import unittest

from capture.completion import (NAMESPACE, sync_goal_completion,
                                goal_completion_payload, acknowledge_goal_completion)
from capture.presentation import parse_goal_command, parse_reset_goal_command

BASE = 22000000
NOW = "2026-10-19T18:00:00Z"
TOKEN = "a" * 32
TOKEN_TWO = "b" * 32


def initial(target=1000000, account="101", base=BASE, since=NOW, generation=0):
    return {"ui_language": "es", "unrelated": {"keep": [1, 2]},
            "account_goals": {"NA:" + account: {"schema": 2, "mode": "balance_growth",
                "target": target, "baseline": base, "since_utc": since,
                "reset_generation": generation}}}


def sync(config, balance, token=TOKEN, account="101"):
    return sync_goal_completion(config, "NA", account, balance, lambda: token) or config


def event(config, balance, account="101"):
    return goal_completion_payload(config, "NA", account, balance)


class GoalCompletionTests(unittest.TestCase):
    def test_armed_goal_crossing_has_one_durable_opaque_event(self):
        saved = initial()
        original = copy.deepcopy(saved)
        armed = sync(saved, BASE)
        self.assertIsNone(event(armed, BASE))
        self.assertEqual(saved, original)
        completed = sync(armed, BASE + 1000000)
        pending = event(completed, BASE + 1000000)
        self.assertEqual(pending, {"id": TOKEN, "account_context": "NA:101",
            "target": 1000000, "reset_generation": 0})
        self.assertIsNone(sync_goal_completion(completed, "NA", "101", BASE + 2000000))
        self.assertEqual(event(completed, BASE + 2000000), pending)
        self.assertEqual({key: value for key, value in completed.items() if key != NAMESPACE}, original)

    def test_preexisting_complete_goal_migrates_silently(self):
        config = sync(initial(), BASE + 1000000)
        self.assertIsNone(event(config, BASE + 1000000))
        self.assertIsNone(sync_goal_completion(config, "NA", "101", BASE + 2000000))
        config = sync(config, BASE - 100)
        self.assertIsNone(event(sync(config, BASE + 1000000), BASE + 1000000))

    def test_ack_is_idempotent_and_recross_cannot_replay(self):
        config = sync(sync(initial(), BASE), BASE + 1000000)
        args = event(config, BASE + 1000000)
        acked = acknowledge_goal_completion(config, "NA", "101", BASE + 1000000, args)
        self.assertIsNone(event(acked, BASE + 1000000))
        self.assertIsNone(acknowledge_goal_completion(acked, "NA", "101", BASE + 1000000, args))
        again = sync(sync(acked, BASE), BASE + 1000000)
        self.assertIsNone(event(again, BASE + 1000000))

    def test_higher_target_earns_new_event_lower_equal_dont_replay(self):
        config = sync(sync(initial(), BASE), BASE + 1000000)
        config = acknowledge_goal_completion(config, "NA", "101", BASE + 1000000,
                                             event(config, BASE + 1000000))
        for value in ("500000", "1000000"):
            config = parse_goal_command(value, "balance_growth", config, NOW, BASE + 1000000, "NA", "101")
            config = sync(config, BASE + 1000000)
            self.assertIsNone(event(config, BASE + 1000000))
        config = parse_goal_command("2000000", "balance_growth", config, NOW, BASE + 1000000, "NA", "101")
        config = sync(config, BASE + 1000000)
        self.assertIsNone(event(config, BASE + 1000000))
        config = sync(config, BASE + 2000000, TOKEN_TWO)
        self.assertEqual(event(config, BASE + 2000000)["id"], TOKEN_TWO)

    def test_target_change_or_disable_discards_old_pending_without_resetting_highwater(self):
        for value in ("0", "500000", "2000000"):
            config = sync(sync(initial(), BASE), BASE + 1000000)
            changed = parse_goal_command(value, "balance_growth", config, NOW, BASE + 1000000, "NA", "101")
            changed = sync(changed, BASE + 1000000)
            self.assertIsNone(event(changed, BASE + 1000000))
            restored = parse_goal_command("1000000", "balance_growth", changed, NOW, BASE + 1000000, "NA", "101")
            self.assertIsNone(event(sync(restored, BASE + 1000000), BASE + 1000000))

    def test_explicit_reset_rearms_even_same_balance_and_second(self):
        config = sync(sync(initial(), BASE), BASE + 1000000)
        old_args = event(config, BASE + 1000000)
        config = parse_reset_goal_command("1000000", "balance_growth", config, NOW,
                                         BASE + 1000000, "NA", "101")
        config = sync(config, BASE + 1000000)
        self.assertIsNone(acknowledge_goal_completion(config, "NA", "101", BASE + 1000000, old_args))
        config = sync(config, BASE + 2000000, TOKEN_TWO)
        self.assertEqual(event(config, BASE + 2000000)["reset_generation"], 1)

    def test_reference_change_and_history_clear_invalidate_pending(self):
        config = sync(sync(initial(), BASE), BASE + 1000000)
        for key, value in (("baseline", BASE + 1000000), ("since_utc", "2026-10-20T18:00:00Z"),
                           ("reset_generation", 1)):
            changed = copy.deepcopy(config)
            changed["account_goals"]["NA:101"][key] = value
            self.assertIsNone(event(changed, BASE + 1000000))
        cleared = copy.deepcopy(config)
        cleared["account_goals"]["NA:101"].update(target=0, baseline=None, since_utc=None)
        self.assertNotIn("NA:101", sync(cleared, BASE + 1000000)[NAMESPACE])

    def test_pending_cancelled_by_loss_does_not_repeat_on_recovery(self):
        completed = sync(sync(initial(), BASE), BASE + 1000000)
        self.assertIsNone(event(completed, BASE))
        dipped = sync(completed, BASE)
        self.assertIsNone(event(sync(dipped, BASE + 1000000), BASE + 1000000))

    def test_no_balance_or_invalid_balance_does_not_arm_complete_or_ack(self):
        for amount in (None, True, -1, 1.5, "23000000"):
            with self.subTest(balance=amount):
                self.assertIsNone(sync_goal_completion(initial(), "NA", "101", amount))
                self.assertIsNone(event(initial(), amount))
        completed = sync(sync(initial(), BASE), BASE + 1000000)
        self.assertIsNone(acknowledge_goal_completion(completed, "NA", "101", None,
                                                     event(completed, BASE + 1000000)))

    def test_foreign_stale_or_malformed_ack_does_not_consume_pending(self):
        config = sync(sync(initial(), BASE), BASE + 1000000)
        args = event(config, BASE + 1000000)
        for request in (None, [], {}, {"id": TOKEN}, dict(args, account_context="NA:102"),
                        dict(args, id=TOKEN_TWO), dict(args, id=True)):
            self.assertIsNone(acknowledge_goal_completion(config, "NA", "101", BASE + 1000000, request))
        self.assertEqual(event(config, BASE + 1000000), args)

    def test_account_isolation_and_language_independence(self):
        config = initial()
        config["account_goals"].update(initial(account="102")["account_goals"])
        config = sync(sync(config, BASE), BASE + 1000000)
        one = event(config, BASE + 1000000)
        config = sync(config, BASE, account="102")
        config = sync(config, BASE + 1000000, TOKEN_TWO, account="102")
        self.assertEqual(event(config, BASE + 1000000), one)
        self.assertEqual(event(config, BASE + 1000000, "102")["id"], TOKEN_TWO)
        config["ui_language"] = "en"
        self.assertEqual(event(config, BASE + 1000000), one)
        acked = acknowledge_goal_completion(config, "NA", "101", BASE + 1000000, one)
        self.assertEqual(event(acked, BASE + 1000000, "102")["id"], TOKEN_TWO)

    def test_corrupt_or_foreign_reference_tracker_is_not_retroactive(self):
        for tracker in (True, {}, {"schema": 1, "reference": {}, "highest_completed_target": 0},
                        {"schema": 1, "highest_completed_target": True}):
            config = initial()
            config[NAMESPACE] = {"NA:101": tracker}
            migrated = sync(config, BASE + 1000000)
            self.assertIsNone(event(migrated, BASE + 1000000))

    def test_invalid_token_factory_cannot_mutate_state(self):
        config = sync(initial(), BASE)
        original = copy.deepcopy(config)
        with self.assertRaises(ValueError):
            sync_goal_completion(config, "NA", "101", BASE + 1000000, lambda: "not-an-id")
        self.assertEqual(config, original)
