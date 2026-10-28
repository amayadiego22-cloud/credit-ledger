import copy
import sys
import types
import unittest
from unittest.mock import patch
from capture.coupons import CouponObserver, coupon_receipt


class CouponTests(unittest.TestCase):
    def setUp(self):
        self.receipts = []
        self.result = types.SimpleNamespace(success=True)
        self.native_calls = []
        self.native_error = None
        test = self
        class Processor:
            event = "battle_pass_tickets"
            count = 2
            def _getLootBox(self):
                return types.SimpleNamespace(getType=lambda:self.event,getUserName=lambda:"Cupón del pase")
            def _getCount(self):
                return self.count
            def _successHandler(self, code, ctx=None):
                test.native_calls.append((self,code,ctx))
                if test.native_error:
                    raise test.native_error
                # The native formatter may mutate the original reward mapping.
                ctx.get("bonus", [{}])[0].pop("credits",None)
                return test.result
        self.processor = Processor
        self.original = Processor._successHandler
        self.owner = types.SimpleNamespace(_alive=True, replay=types.SimpleNamespace(isPlaying=lambda:False),
                   accept_receipt=self.receipts.append)
        common = types.ModuleType("battle_pass_common")
        common.BATTLE_PASS_TICKETS_EVENT = "battle_pass_tickets"
        processors = types.ModuleType("gui.shared.gui_items.processors.loot_boxes")
        processors.LootBoxSystemOpenProcessor = Processor
        self.modules = patch.dict(sys.modules,{"battle_pass_common":common,"gui.shared.gui_items.processors.loot_boxes":processors})
        self.modules.start()
        self.observer = CouponObserver(self.owner)

    def tearDown(self):
        self.observer.close()
        self.modules.stop()

    def test_real_request_slots_are_summed_before_native_formatting_and_return_preserved(self):
        ctx = {"bonus":[{"credits":50000},{"credits":20000,"freeXP":1000}]}
        instance = self.processor()
        result = instance._successHandler(0,ctx)
        self.assertIs(result,self.result)
        self.assertEqual(len(self.native_calls),1)
        self.assertEqual(self.receipts[0]["credits"],70000)
        self.assertIn("Cupón del pase",self.receipts[0]["title"])
        self.assertFalse(self.receipts[0]["included_in_battle"])
        first_id = self.receipts[0]["id"]
        instance._successHandler(0,{"bonus":[{"credits":50000},{"credits":20000}]})
        self.assertEqual(self.receipts[-1]["id"],first_id)
        self.processor()._successHandler(0,{"bonus":[{"credits":70000}]})
        self.assertNotEqual(self.receipts[-1]["id"],first_id)

    def test_failed_result_and_other_box_events_are_not_labeled_as_vouchers(self):
        self.result.success=False
        self.processor()._successHandler(0,{"bonus":[{"credits":50000}]})
        self.result.success=True
        instance=self.processor()
        instance.event="another_event"
        instance._successHandler(0,{"bonus":[{"credits":50000}]})
        self.assertEqual(self.receipts,[])
        self.assertEqual(len(self.native_calls),2)

    def test_native_exception_and_receipt_failure_do_not_change_native_outcome(self):
        self.native_error=RuntimeError("native failure")
        with self.assertRaisesRegex(RuntimeError,"native failure"):
            self.processor()._successHandler(0,{"bonus":[{"credits":50000}]})
        self.assertEqual(self.receipts,[])
        self.native_error=None
        def failed_save(_):raise OSError("synthetic ledger failure")
        self.owner.accept_receipt=failed_save
        with patch("capture.coupons.traceback.print_exc"),patch("builtins.print"):
            self.assertIs(self.processor()._successHandler(0,{"bonus":[{"credits":50000}]}),self.result)

    def test_close_restores_only_our_wrapper_and_other_mod_chains_keep_native_calls(self):
        ours=self.processor._successHandler
        def other(instance,code,ctx=None):return ours(instance,code,ctx)
        self.processor._successHandler=other
        self.observer.close()
        self.assertIs(self.processor._successHandler,other)
        self.processor()._successHandler(0,{"bonus":[{"credits":50000}]})
        self.assertEqual(self.receipts,[])
        self.assertEqual(len(self.native_calls),1)

    def test_unknown_credit_shapes_are_not_invented_or_rounded(self):
        for value in (True,"50000",50000.5,{},-10):
            self.assertIsNone(coupon_receipt({"bonus":[{"credits":value}]},"id","",1,"2026-10-18T06:00:00Z"))
        self.assertIsNone(coupon_receipt({"bonus":[{"freeXP":500}]},"id","",1,"2026-10-18T06:00:00Z"))


if __name__ == "__main__":unittest.main()
