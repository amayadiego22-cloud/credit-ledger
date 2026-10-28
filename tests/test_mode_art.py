"""Native emblems follow each result's bonus type without changing money."""
import copy
import unittest

from capture.battle_modes import battle_mode_icon, battle_mode_payload, _MODE_LABELS
from capture.presentation import build_payload
from core.ledger import EconomyLedger
from test_mode_filters import result


class ModeArtTests(unittest.TestCase):
    def test_every_known_mode_has_its_native_local_art(self):
        for code in _MODE_LABELS:
            icon = battle_mode_icon(code)
            self.assertTrue(icon.startswith("coui://"))
            self.assertIn("/gui/maps/icons/battleTypes/", icon[6:])
            self.assertTrue(icon.endswith(".png"))
            self.assertNotIn("..", icon)

    def test_primary_emblems_match_installed_selector_paths(self):
        for code, path in (
                (1, "gui/maps/icons/battleTypes/64x64/random.png"),
                (14, "gui/maps/icons/battleTypes/64x64/specBattlesList.png"),
                (15, "gui/maps/icons/battleTypes/64x64/specBattlesList.png"),
                (20, "gui/maps/icons/battleTypes/64x64/strongholdsBattlesList.png"),
                (21, "gui/maps/icons/battleTypes/64x64/strongholdsBattlesList.png"),
                (43, "gui/maps/icons/battleTypes/64x64/comp7.png"),
                (49, "comp7_light/gui/maps/icons/battleTypes/64x64/comp7_light.png")):
            self.assertEqual(battle_mode_icon(code), "coui://" + path)
        for code in (101, 102, 103):
            self.assertEqual(battle_mode_icon(code),
                "coui://halloween/gui/maps/icons/battleTypes/64x64/halloween.extend.png")

    def test_unknown_or_invalid_identity_cannot_take_another_modes_emblem(self):
        for code in (None, True, False, "1", 1.0, -1, 0, 999, 2147483648):
            self.assertIsNone(battle_mode_icon(code))
        self.assertIsNone(battle_mode_payload({"bonus_type": 999})["icon"])
        self.assertIsNone(battle_mode_payload({"bonus_type": 1, "icon": "https://example.com/logo.png"}))

    def test_group_selected_battle_and_vehicle_query_agree_without_financial_changes(self):
        ledger = EconomyLedger()
        for number, code in enumerate((1, 20, 43, 102, 999), 1):
            row = result(number, code)
            row["vehicles"] = [{"vehicle_type_id": "321", "name": "Tanque de prueba",
                                "tier": 8, "icon": None}]
            ledger.upsert_result(row)
        before = copy.deepcopy(ledger.to_dict())
        config = {"account_goals": {"NA:101": {"schema": 2, "mode": "balance_growth",
                  "target": 100000, "baseline": 22000000, "since_utc": "2026-10-18T12:00:00Z"}}}
        payload = build_payload(ledger, "NA", "101", config, 22100000,
            vehicle_filter={"mode_key": "mode:102", "vehicle_key": "vehicle:321", "request_id": 1})
        for group in payload["mode_groups"]:
            icon = battle_mode_icon(int(group["key"][5:]))
            self.assertEqual(group["icon"], icon)
            for row in group["history"]:
                self.assertEqual(row["battle_mode"]["icon"], icon)
        self.assertEqual(payload["vehicle_selection"]["history"][0]["battle_mode"]["icon"], battle_mode_icon(102))
        self.assertEqual(payload["summary"]["net_credits"], ledger.summary("NA", "101")["net_credits"])
        self.assertEqual(ledger.to_dict(), before)
        payload["history"][0]["battle_mode"]["icon"] = None
        self.assertEqual(ledger.to_dict(), before)


if __name__ == "__main__":
    unittest.main()
