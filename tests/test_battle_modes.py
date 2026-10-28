# -*- coding: utf-8 -*-
import copy
import unittest

from capture.battle_modes import battle_mode_from_common, battle_mode_payload, battle_mode_icon
from capture.normalizer import normalize_snapshot
from capture.snapshot import make_snapshot
from capture.native import derive_credits
from capture.presentation import build_payload
from core.ledger import EconomyLedger, LedgerValidationError
from test_native_finance import Reusable
from test_snapshot import fixture


def snapshot(common=None):
    raw = fixture()
    if common is not None:
        raw["common"].update(common)
    result = make_snapshot(raw, "NA")
    result["native_credits"] = derive_credits(raw, lambda _: Reusable())
    return result


def record(mode=None):
    result = normalize_snapshot(snapshot())
    if mode is not None:
        result["battle_mode"] = mode
    return result


class BattleModeTests(unittest.TestCase):
    def test_primary_native_modes_have_separate_labels(self):
        for code, label in ((1, u"Batalla aleatoria"), (20, u"Escaramuza"),
                            (21, u"Avance"), (43, u"Asedio")):
            self.assertEqual(battle_mode_payload({"bonus_type": code})["label"], label)

    def test_verified_additional_native_modes_have_friendly_spanish_labels(self):
        for code, label in ((2, u"Entrenamiento en equipo"), (4, u"Batalla especial"),
                            (5, u"Batalla especial"), (7, u"Batalla de equipo"),
                            (9, u"Modo de juego especial"), (13, u"Mapa global"),
                            (14, u"Batalla de torneo"), (15, u"Torneo de clanes"),
                            (18, u"Dominación"), (19, u"Cacería de acero"),
                            (22, u"Batalla clasificatoria"), (24, u"Gran batalla"),
                            (27, u"Línea del frente"), (29, u"Cazador de acero"),
                            (37, u"Misión de reconocimiento"), (38, u"Topografía"),
                            (44, u"Entrada en calor"), (49, u"Asedio ligero")):
            self.assertEqual(battle_mode_payload({"bonus_type": code})["label"], label)

    def test_halloween_bonus_type_is_separate_from_last_stand_gui_type(self):
        for code, label in ((101, u"Torre oscura · Normal"),
                            (102, u"Torre oscura · Difícil"),
                            (103, u"Torre oscura · Pesadilla")):
            self.assertEqual(battle_mode_payload({"bonus_type": code})["label"], label)
        self.assertEqual(battle_mode_payload(battle_mode_from_common(
            {"bonusType": 1, "guiType": 102}))["label"], u"Batalla aleatoria")

    def test_bonus_type_is_canonical_and_arena_alias_is_only_fallback(self):
        self.assertEqual(battle_mode_from_common({"bonusType": 20, "arenaBonusType": 1}),
                         {"bonus_type": 20})
        self.assertEqual(battle_mode_from_common({"arenaBonusType": 43}), {"bonus_type": 43})
        self.assertIsNone(battle_mode_from_common({"bonusType": True, "arenaBonusType": 1}))

    def test_gui_type_is_separate_metadata_without_mode_inference(self):
        self.assertEqual(battle_mode_from_common({"bonusType": 20, "guiType": 43}),
                         {"bonus_type": 20, "gui_type": 43})
        self.assertIsNone(battle_mode_from_common({"guiType": 43}))
        self.assertEqual(battle_mode_from_common({"bonusType": 20, "guiType": "43"}),
                         {"bonus_type": 20})

    def test_missing_malformed_or_unbounded_codes_are_not_guessed(self):
        for common in (None, [], "1", {}, {"arenaBonusType": None}):
            self.assertIsNone(battle_mode_from_common(common))
        for value in (True, False, -1, 2147483648, "20", 20.0, [], {}):
            self.assertIsNone(battle_mode_from_common({"bonusType": value}))
        self.assertEqual(battle_mode_from_common({"bonusType": 0}), {"bonus_type": 0})
        self.assertEqual(battle_mode_from_common({"bonusType": 2147483647}),
                         {"bonus_type": 2147483647})

    def test_unknown_native_codes_keep_exact_identity_and_generic_label(self):
        source = {"bonus_type": 2147483647, "gui_type": 99}
        payload = battle_mode_payload(source)
        self.assertEqual(payload["label"], u"Modo no identificado (código 2147483647)")
        self.assertEqual(payload["bonus_type"], 2147483647)
        payload["gui_type"] = 7
        self.assertEqual(source["gui_type"], 99)

    def test_payload_rejects_invalid_or_prelabelled_mode_metadata(self):
        for mode in (None, [], {}, {"gui_type": 43}, {"bonus_type": "1"},
                     {"bonus_type": 1, "gui_type": None},
                     {"bonus_type": 1, "label": "Arbitrary"}):
            self.assertIsNone(battle_mode_payload(mode))

    def test_snapshot_captures_only_native_battle_context(self):
        raw = fixture()
        raw["common"].update(bonusType=20, arenaBonusType=21, guiType=9,
                             players="PRIVATE", accountDBID=999, selectedMode=43)
        original = copy.deepcopy(raw)
        captured = make_snapshot(raw, "NA")
        self.assertEqual(captured["common"], {"arenaCreateTime": 1792242000,
                         "duration": 300, "bonusType": 20, "arenaBonusType": 21, "guiType": 9})
        self.assertEqual(raw, original)

    def test_normalizer_preserves_financial_totals_and_input(self):
        source = snapshot({"bonusType": 20, "guiType": 9})
        before = copy.deepcopy(source)
        observed = normalize_snapshot(source)
        baseline = normalize_snapshot(snapshot())
        self.assertEqual(observed["battle_mode"], {"bonus_type": 20, "gui_type": 9})
        self.assertEqual(observed["credits"], baseline["credits"])
        self.assertEqual(observed["occurred_at"], baseline["occurred_at"])
        self.assertEqual(source, before)
        self.assertIsNone(baseline["battle_mode"])

    def test_legacy_records_round_trip_with_unknown_mode(self):
        old = record()
        old.pop("battle_mode")
        ledger = EconomyLedger()
        ledger.upsert_result(old)
        restored = EconomyLedger.from_dict(ledger.to_dict())
        self.assertIsNone(restored.list_results()[0]["battle_mode"])
        self.assertEqual(restored.summary("NA", "101")["net_credits"], 51500)
        self.assertIsNone(build_payload(restored, "NA", "101", {}, None)["history"][0]["battle_mode"])

    def test_persisted_shape_requires_bounded_exact_integer_codes(self):
        for mode in ([], "20", {}, {"gui_type": 1}, {"bonus_type": 20, "label": "Escaramuza"}):
            with self.assertRaises(LedgerValidationError):
                EconomyLedger().upsert_result(record(mode))
        for key in ("bonus_type", "gui_type"):
            for value in (None, True, False, -1, 2147483648, 20.0, "20", [], {}):
                mode = {"bonus_type": 20, "gui_type": 9}
                mode[key] = value
                with self.assertRaises(LedgerValidationError):
                    EconomyLedger().upsert_result(record(mode))

    def test_duplicate_missing_mode_keeps_recovered_identity(self):
        ledger = EconomyLedger()
        ledger.upsert_result(record({"bonus_type": 20, "gui_type": 9}))
        self.assertEqual(ledger.upsert_result(record()), "unchanged")
        self.assertEqual(ledger.list_results()[0]["battle_mode"], {"bonus_type": 20, "gui_type": 9})
        self.assertEqual(ledger.summary("NA", "101")["battle_count"], 1)

    def test_same_mode_preserves_gui_metadata_but_explicit_correction_can_replace(self):
        ledger = EconomyLedger()
        ledger.upsert_result(record({"bonus_type": 20, "gui_type": 9}))
        self.assertEqual(ledger.upsert_result(record({"bonus_type": 20})), "unchanged")
        self.assertEqual(ledger.upsert_result(record({"bonus_type": 43})), "updated")
        self.assertEqual(ledger.list_results()[0]["battle_mode"], {"bonus_type": 43})
        self.assertEqual(ledger.summary("NA", "101")["net_credits"], 51500)

    def test_mode_enrichment_and_ui_metadata_are_copied_and_account_scoped(self):
        row = record({"bonus_type": 20, "gui_type": 9})
        ledger = EconomyLedger()
        ledger.upsert_result(row)
        row["battle_mode"]["bonus_type"] = 1
        foreign = record({"bonus_type": 43})
        foreign["account_id"] = "999"
        ledger.upsert_result(foreign)
        payload = build_payload(ledger, "NA", "101", {}, None)
        self.assertEqual(len(payload["history"]), 1)
        self.assertEqual(payload["history"][0]["battle_mode"],
                         {"bonus_type": 20, "gui_type": 9, "label": u"Escaramuza",
                          "icon": battle_mode_icon(20)})
        payload["history"][0]["battle_mode"]["bonus_type"] = 43
        self.assertEqual(ledger.list_results("NA", "101")[0]["battle_mode"]["bonus_type"], 20)

    def test_pending_notification_cannot_change_final_battle_mode_or_totals(self):
        ledger = EconomyLedger()
        ledger.upsert_result(record({"bonus_type": 20}))
        pending = record({"bonus_type": 43})
        pending.update(status="pending", credits=None)
        self.assertEqual(ledger.upsert_result(pending), "ignored_pending")
        self.assertEqual(ledger.list_results()[0]["battle_mode"], {"bonus_type": 20})
        self.assertEqual(ledger.summary("NA", "101")["net_credits"], 51500)


if __name__ == "__main__":
    unittest.main()
