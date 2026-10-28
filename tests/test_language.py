"""Live language changes are presentation preferences, never money transactions."""
import copy
import sys
import types
import unittest
from unittest.mock import patch

from capture.localization import language, localize_payload, translate
from capture.presentation import build_payload
from capture.runtime import credits_text
from capture.storage import read_json
from capture.wallet import WalletBook
from core import EconomyLedger
import test_capture_runtime as harness
from test_presentation import observed_record
from timezone_fixtures import mock_local_timezone


class LanguagePresentationTests(unittest.TestCase):
    def test_saved_tournament_modes_render_in_current_and_archived_filters_without_rewriting_records(self):
        from test_daily_archive import result, CLOCK, NOW
        ledger = EconomyLedger()
        for code in (14, 15):
            for suffix, occurred in ((0, "2026-10-20T14:00:00Z"), (1, "2026-10-19T14:00:00Z")):
                row = result(code * 10 + suffix, occurred=occurred, mode=code)
                row["battle_mode"]["gui_type"] = 0
                ledger.upsert_result(row)
        original = copy.deepcopy(ledger.to_dict())
        config = {"account_history": {"NA:101": {"mode": "server", "clock": "server_v1",
            "server_cycle": CLOCK["cycle_start_utc"], "since_utc": CLOCK["cycle_start_utc"],
            "baseline": 22000000, "generation": 4, "excluded_battles": []}}}
        expected_icon = "coui://gui/maps/icons/battleTypes/64x64/specBattlesList.png"
        for code, es, en in ((14, "Batalla de torneo", "Tournament Battle"),
                            (15, "Torneo de clanes", "Clan Tournament")):
            for selected, label in (("es", es), ("en", en)):
                settings = dict(config, ui_language=selected)
                payload = build_payload(ledger, "NA", "101", settings, 22000000,
                    now_utc=NOW, server_clock=CLOCK,
                    vehicle_filter={"mode_key": "mode:%s" % code, "vehicle_key": "vehicle:321", "request_id": 1},
                    archive_filter={"day_key": "2026-10-19T10:00:00Z", "mode_key": "mode:%s" % code,
                                    "vehicle_key": "vehicle:321", "request_id": 2})
                self.assertEqual(payload["summary"]["net_credits"], 130000)
                group = next(g for g in payload["mode_groups"] if g["key"] == "mode:%s" % code)
                self.assertEqual((group["label"], group["icon"]), (label, expected_icon))
                for scoped in (payload["vehicle_selection"], payload["history_archive"]["selection"]):
                    self.assertEqual(scoped["history_total"], 1)
                    self.assertEqual(scoped["summary"]["net_credits"], 65000)
                    mode = scoped["history"][0]["battle_mode"]
                    self.assertEqual(mode, {"bonus_type": code, "gui_type": 0,
                                           "label": label, "icon": expected_icon})
                self.assertEqual(ledger.to_dict(), original)
                self.assertNotIn("ui_language", config)

    def test_spanish_is_default_for_missing_and_invalid_saved_preferences(self):
        for value in (None, {}, {"ui_language": "fr"}, {"ui_language": "EN"},
                      {"ui_language": True}, {"ui_language": []}, {"ui_language": {}}):
            self.assertEqual(language(value), "es")
        for selected in ("es", "en"):
            self.assertEqual(language({"ui_language": selected}), selected)

    def test_english_payload_covers_messages_errors_modes_fallbacks_dates_and_rewards(self):
        ledger = EconomyLedger()
        record = observed_record()
        record["vehicles"] = [{"vehicle_type_id": "321", "name": "Vehículo 321",
                               "tier": 11, "icon": None}]
        record["battle_mode"] = {"bonus_type": 20}
        ledger.upsert_result(record)
        config = {"ui_language": "en"}
        wallet = WalletBook()
        wallet.observe("NA", "101", 22000000, "2026-10-18T00:00:00Z")
        wallet.upsert_receipt("NA", "101", {
            "id": "tokenQuests:7", "kind": "tokenQuests", "credits": 3000,
            "title": "Misión / recompensa", "occurred_at": "2026-10-18T01:00:00Z",
            "battle_id": None, "included_in_battle": False,
            "parts": [{"quest_id": "unknown-7", "title": "Misión unknown-7",
                       "credits": 3000, "name_resolved": False}]})
        original = copy.deepcopy((ledger.to_dict(), config, wallet.data))
        with mock_local_timezone("America/Bogota"):
            payload = build_payload(ledger, "NA", "101", config, None,
                error="El vehículo seleccionado no es válido.", wallet=wallet)
        self.assertEqual(payload["language"], "en")
        self.assertIn("balance is still syncing", payload["message"])
        self.assertEqual(payload["error"], "The selected vehicle is invalid.")
        self.assertEqual(payload["history"][0]["battle_mode"]["label"], "Skirmish")
        self.assertEqual(payload["history"][0]["vehicles"][0]["name"], "Vehicle 321")
        self.assertEqual(payload["vehicle_groups"][0]["label"], "Vehicle 321")
        self.assertEqual(payload["history"][0]["time_label"], "17 Oct 19:40")
        self.assertEqual(payload["rewards"][0]["title"], "Mission / reward")
        self.assertEqual(payload["rewards"][0]["parts"][0]["title"], "Mission unknown-7")
        self.assertEqual((ledger.to_dict(), config, wallet.data), original)
        self.assertEqual(payload["summary"]["net_credits"], -113508)

    def test_native_names_are_kept_and_only_generated_wrappers_are_translated(self):
        payload = {"vehicles": [{"name": "Avispa", "vehicle_type_id": "7"}],
            "rewards": [{"quest_id": "1", "name_resolved": True, "title": "La misión del héroe"},
                        {"quest_id": "2", "name_resolved": True,
                         "title": "Crisol: Nombre nativo | Misión 3"},
                        {"kind": "battlePassVoucher", "title": "Raspado de cupón del Pase de batalla: Nombre nativo (x3)"}],
            "mode_groups": [{"key": "mode:102", "label": "old"},
                            {"key": "mode:999", "label": "old"},
                            {"key": "unknown", "label": "old"}],
            "vehicle_groups": [{"key": "unknown", "label": "old"},
                               {"key": "multiple", "label": "old"}]}
        localize_payload(payload, {"ui_language": "en"})
        self.assertEqual(payload["vehicles"][0]["name"], "Avispa")
        self.assertEqual(payload["rewards"][0]["title"], "La misión del héroe")
        self.assertEqual(payload["rewards"][1]["title"], "Crucible: Nombre nativo | Mission 3")
        self.assertEqual(payload["rewards"][2]["title"], "Battle Pass voucher scratch reward: Nombre nativo (x3)")
        self.assertEqual([m["label"] for m in payload["mode_groups"]],
                         ["Dark Tower · Hard", "Unidentified mode (code 999)", "Unidentified mode"])
        self.assertEqual([v["label"] for v in payload["vehicle_groups"]],
                         ["Unidentified vehicle", "Multiple vehicles"])

    def test_english_dates_include_unambiguous_month_and_local_timezone(self):
        payload = {"goal": {"since_utc": "2026-10-18T05:00:00Z", "since_label": "old"},
            "history_archive": {"days": [{"key": "2026-10-18T10:00:00Z", "label": "old"}],
             "selection": {"day_key": "2026-10-18T10:00:00Z", "label": "old"}}}
        with mock_local_timezone("America/Bogota"):
            localize_payload(payload, {"ui_language": "en"})
        self.assertEqual(payload["goal"]["since_label"], "18 Oct 2026 00:00 (local time, UTC-05:00)")
        self.assertEqual(payload["history_archive"]["days"][0]["label"], "18 Oct 2026")
        self.assertEqual(payload["history_archive"]["selection"]["label"], "18 Oct 2026")

    def test_loading_account_and_number_notices_have_localized_english(self):
        self.assertEqual(build_payload(EconomyLedger(), "NA", None,
             {"ui_language": "en"}, None)["message"], "Waiting for your game account to sync.")
        self.assertEqual(credits_text(-113508), "-113.508")
        self.assertEqual(credits_text(-113508, "en"), "-113,508")
        self.assertEqual(translate("Selecciona español o inglés.", "en"), "Choose Spanish or English.")


class LanguageRuntimeTests(unittest.TestCase):
    setUp = harness.RuntimeTests.setUp
    tearDown = harness.RuntimeTests.tearDown

    def request(self, selected="en", identity=1):
        return {"language": selected, "request_id": identity}

    def test_change_is_atomic_persistent_and_refreshes_same_view_without_resetting_finance(self):
        self.balance = 22000000
        self.collector.save_goal({"value": "3000000", "mode": "balance_growth"})
        before = copy.deepcopy(self.collector.config)
        wallet = copy.deepcopy(self.collector.wallet.data)
        ledger = copy.deepcopy(self.collector.ledger.to_dict())
        model = object()
        self.collector.panel.model = model
        refreshes = []
        self.collector.panel.refresh = lambda **kwargs: refreshes.append(kwargs)
        self.collector.set_language(self.request(identity="1"))
        expected = copy.deepcopy(before)
        expected["ui_language"] = "en"
        self.assertEqual(self.collector.config, expected)
        self.assertEqual(read_json(self.collector.config_path), expected)
        self.assertIs(self.collector.panel.model, model)
        self.assertEqual(refreshes, [{"force": True}])
        self.assertEqual(self.collector.wallet.data, wallet)
        self.assertEqual(self.collector.ledger.to_dict(), ledger)
        payload = self.collector.panel_payload()
        self.assertEqual(payload["language"], "en")
        self.assertEqual(payload["language_selection"], {"request_id": 1,
             "requested_language": "en", "language": "en", "available": True, "error": None})

    def test_failed_save_keeps_previous_language_and_all_financial_settings(self):
        self.collector.set_language(self.request())
        before = copy.deepcopy(self.collector.config)
        with patch("capture.runtime.atomic_json", side_effect=OSError("test failed write")):
            self.collector.set_language(self.request("es", 2))
        self.assertEqual(self.collector.config, before)
        self.assertEqual(read_json(self.collector.config_path), before)
        payload = self.collector.panel_payload()
        self.assertEqual(payload["language"], "en")
        ack = payload["language_selection"]
        self.assertEqual(ack["requested_language"], "es")
        self.assertFalse(ack["available"])
        self.assertEqual(ack["error"], "The language could not be saved. Your previous selection has been kept.")

    def test_language_ack_never_overwrites_errors_or_state_of_other_pending_actions(self):
        self.balance = 22000000
        self.collector.save_goal({"value": "3000000", "mode": "balance_growth"})
        self.collector.panel_error = "Existing vehicle request error"
        self.collector._vehicle_filter = {"request_id": 7, "vehicle_key": "vehicle:321"}
        self.collector._archive_filter = {"request_id": 9, "day_key": "2026-10-18T10:00:00Z"}
        financial = copy.deepcopy((self.collector.config, self.collector.wallet.data,
                                   self.collector.ledger.to_dict()))
        filters = copy.deepcopy((self.collector._vehicle_filter, self.collector._archive_filter))
        self.collector.set_language(self.request())
        self.assertEqual(self.collector.panel_error, "Existing vehicle request error")
        self.assertTrue(self.collector._language_selection["available"])
        self.collector.set_language(self.request("unsupported", 2))
        self.assertEqual(self.collector.panel_error, "Existing vehicle request error")
        self.assertFalse(self.collector._language_selection["available"])
        with patch("capture.runtime.atomic_json", side_effect=OSError("test language write failure")):
            self.collector.set_language(self.request("es", 3))
        self.assertEqual(self.collector.panel_error, "Existing vehicle request error")
        self.assertFalse(self.collector._language_selection["available"])
        self.assertEqual(self.collector._language_selection["requested_language"], "es")
        expected = financial[0]
        expected["ui_language"] = "en"
        self.assertEqual(self.collector.config, expected)
        self.assertEqual(self.collector.wallet.data, financial[1])
        self.assertEqual(self.collector.ledger.to_dict(), financial[2])
        self.assertEqual((self.collector._vehicle_filter, self.collector._archive_filter), filters)

    def test_invalid_preferences_and_commands_never_silently_change_or_write_language(self):
        self.collector.config["ui_language"] = "fr"
        before = copy.deepcopy(self.collector.config)
        with patch("capture.runtime.atomic_json") as save:
            for i, value in enumerate(("fr", "EN", "", True, None, [], {}), 1):
                self.collector.set_language(self.request(value, i))
                self.assertFalse(self.collector._language_selection["available"])
            self.collector.set_language(None)
            save.assert_not_called()
        self.assertEqual(self.collector.config, before)
        self.assertEqual(language(self.collector.config), "es")
        self.collector.set_language(self.request("es", 10))
        self.assertEqual(read_json(self.collector.config_path)["ui_language"], "es")

    def test_monotonic_ids_and_model_replacement_ignore_stale_queries_and_acks(self):
        self.collector.panel.model = object()
        self.collector.set_language(self.request("en", 2.0))
        self.collector.set_language(self.request("es", 1))
        self.assertEqual(language(self.collector.config), "en")
        self.collector.panel.model = object()
        self.assertIsNone(self.collector.panel_payload()["language_selection"])
        self.collector.set_language(self.request("es", 1))
        self.assertEqual(language(self.collector.config), "es")
        self.assertEqual(self.collector._language_selection["request_id"], 1)

    def test_invalid_request_ids_do_not_change_language(self):
        for value in (True, 0, 1.5, "01", " 1", float("inf"), [], 9007199254740992):
            self.collector.set_language(self.request(identity=value))
            self.assertEqual(language(self.collector.config), "es")
            self.assertFalse(self.collector._language_selection["available"])

    def test_return_to_spanish_preserves_goal_history_and_filter_state(self):
        self.collector._vehicle_filter = {"request_id": 3, "vehicle_key": "vehicle:321"}
        self.collector._archive_filter = {"request_id": 4, "day_key": "2026-10-18T10:00:00Z"}
        filters = copy.deepcopy((self.collector._vehicle_filter, self.collector._archive_filter))
        self.collector.set_language(self.request())
        self.collector.set_language(self.request("es", 2))
        self.assertEqual((self.collector._vehicle_filter, self.collector._archive_filter), filters)
        self.assertEqual(language(self.collector.config), "es")

    def test_idempotent_saved_choice_acknowledges_without_writing_again(self):
        self.collector.set_language(self.request())
        with patch("capture.runtime.atomic_json") as save:
            self.collector.set_language(self.request("en", 2))
            save.assert_not_called()
        self.assertTrue(self.collector._language_selection["available"])

    def test_system_notifications_and_battle_summary_change_immediately(self):
        messages = []
        gui = types.ModuleType("gui")
        gui.SystemMessages = types.SimpleNamespace(pushMessage=lambda message, **kwargs: messages.append(message),
                                 SM_TYPE=types.SimpleNamespace(Information=1))
        self.collector.set_language(self.request())
        with patch.dict(sys.modules, {"gui": gui}):
            self.collector._notify("Contabilidad: resultado guardado; desglose pendiente de conciliación.")
            record = observed_record()
            self.collector._result_notice(record)
        self.assertIn("Credit Ledger", messages[0])
        self.assertIn("Net: -113,508 credits", messages[1])
        self.assertIn("Repairs: 33,136", messages[1])
        self.assertIn("No active goal", messages[1])


if __name__ == "__main__":
    unittest.main()
