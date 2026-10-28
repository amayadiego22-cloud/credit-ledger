# -*- coding: utf-8 -*-
"""Observe successful native Battle Pass voucher openings without changing them."""
import datetime
import traceback
import uuid
from .wallet import exact_amount, safe_text


def coupon_receipt(context, receipt_id, title, count, now):
    bonuses = context.get("bonus") if isinstance(context, dict) else None
    if not isinstance(bonuses, (list, tuple)):
        return None
    credits = 0
    for reward in bonuses:
        if not isinstance(reward, dict):
            return None
        if "credits" in reward:
            amount = exact_amount(reward["credits"])
            if amount is None or amount < 0:
                return None
            credits += amount
    if credits <= 0:
        return None
    name = u"Raspado de cup\u00f3n del Pase de batalla"
    if title:
        name += u": " + safe_text(title)
    if exact_amount(count) is not None and count > 1:
        name += u" (x%s)" % count
    return {"id": "coupon:" + receipt_id, "kind": "battlePassVoucher", "occurred_at": now,
            "battle_id": None, "credits": credits, "included_in_battle": False,
            "title": name, "parts": []}


class CouponObserver(object):
    def __init__(self, owner):
        from battle_pass_common import BATTLE_PASS_TICKETS_EVENT
        from gui.shared.gui_items.processors.loot_boxes import LootBoxSystemOpenProcessor
        self.owner = owner
        self.processor_class = LootBoxSystemOpenProcessor
        original = LootBoxSystemOpenProcessor._successHandler
        self.original = getattr(original, "im_func", original)
        self.active = True
        observer = self

        def wrapped(processor, code, ctx=None):
            receipt = None
            if observer.active and owner._alive and not owner.replay.isPlaying():
                try:
                    box = processor._getLootBox()
                    if box is not None and box.getType() == BATTLE_PASS_TICKETS_EVENT:
                        # One native request processor represents one actual opening.
                        # Repeated handling on that instance keeps the same local ID.
                        identity = getattr(processor, "_credit_ledger_coupon_id", None)
                        if identity is None:
                            identity = uuid.uuid4().hex
                            processor._credit_ledger_coupon_id = identity
                        now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                        receipt = coupon_receipt(ctx, identity, box.getUserName(), processor._getCount(), now)
                except Exception:
                    print("[CreditLedger] voucher receipt extraction unavailable")
                    traceback.print_exc()
            # Preserve native return values and exceptions. Only a successful
            # native result may be committed as a credit receipt.
            result = observer.original(processor, code, ctx)
            if receipt is not None and getattr(result, "success", False):
                try:
                    first_time = getattr(processor, "_credit_ledger_coupon_time", None)
                    if first_time is None:
                        processor._credit_ledger_coupon_time = receipt["occurred_at"]
                    else:
                        receipt["occurred_at"] = first_time
                    owner.accept_receipt(receipt)
                except Exception:
                    print("[CreditLedger] voucher receipt could not be stored")
                    traceback.print_exc()
            return result

        self.wrapper = wrapped
        LootBoxSystemOpenProcessor._successHandler = wrapped

    def close(self):
        self.active = False
        current = self.processor_class._successHandler
        if getattr(current, "im_func", current) is self.wrapper:
            self.processor_class._successHandler = self.original
