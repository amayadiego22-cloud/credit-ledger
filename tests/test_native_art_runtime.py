"""Current event art refreshes old visible results, never their finances."""
import copy
import types
import unittest
from unittest.mock import patch

import test_capture_runtime as harness
from capture.vehicles import local_icon
from core.ledger import EconomyLedger, LedgerValidationError
from test_mode_filters import result


EVENT = "coui://halloween/gui/maps/icons/vehicle/usa-A100_T49_Halloween_event.extend.png"


class NativeArtRuntimeTests(unittest.TestCase):
    setUp = harness.RuntimeTests.setUp
    tearDown = harness.RuntimeTests.tearDown

    def test_event_art_round_trip_and_backfill_beyond_100_keep_money_exact(self):
        for number in range(1, 107):
            row = result(number, 102 if number == 1 else 1)
            row["vehicles"] = [{"vehicle_type_id": "321", "name": "Granadero",
                                "tier": 9, "icon": None}]
            self.collector.ledger.upsert_result(row)
        before = copy.deepcopy(self.collector.ledger.to_dict())
        native = types.SimpleNamespace(userName="Granadero", level=9, icon=EVENT)
        with patch.object(self.collector, "_vehicle_item", return_value=native) as getter:
            payload = self.collector.panel_payload()
        getter.assert_called_once_with(321)
        mode = next(group for group in payload["mode_groups"] if group["key"] == "mode:102")
        self.assertEqual(mode["history"][0]["vehicles"][0]["icon"], EVENT)
        self.assertEqual(mode["vehicle_groups"][0]["vehicle"]["tier"], 9)
        after = self.collector.ledger.to_dict()
        for old, new in zip(before["records"], after["records"]):
            old.pop("vehicles"); new.pop("vehicles")
            self.assertEqual(old, new)
        restored = EconomyLedger.load(self.collector.ledger_path)
        self.assertEqual(restored.list_results()[0]["vehicles"][0]["icon"], EVENT)

    def test_foreign_account_is_not_refreshed_by_current_accounts_art(self):
        own, other = result(1, 102), result(2, 102, account="999")
        for row in (own, other):
            row["vehicles"] = [{"vehicle_type_id": "321", "name": "Vehículo 321", "tier": None, "icon": None}]
            self.collector.ledger.upsert_result(row)
        foreign = copy.deepcopy(self.collector.ledger.list_results("NA", "999"))
        with patch.object(self.collector, "_vehicle_item", return_value=types.SimpleNamespace(
                userName="Granadero", level=9, icon=EVENT)):
            self.collector._enrich_vehicle_history("101", [])
        self.assertEqual(self.collector.ledger.list_results("NA", "999"), foreign)

    def test_new_local_mount_does_not_allow_arbitrary_files_or_other_mounts(self):
        self.assertEqual(local_icon(EVENT), EVENT)
        for path in (EVENT.replace("halloween/", "private/"), EVENT.replace("vehicle/", "vehicle/../"),
                     EVENT.replace("vehicle/", "settings/"), EVENT + "?token=secret"):
            self.assertIsNone(local_icon(path))
            row = result(1, 102)
            row["vehicles"] = [{"vehicle_type_id": "321", "name": "Granadero", "tier": 9, "icon": path}]
            with self.assertRaises(LedgerValidationError):
                EconomyLedger().upsert_result(row)


if __name__ == "__main__":
    unittest.main()
