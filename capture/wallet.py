# -*- coding: utf-8 -*-
"""Account balance observations and native reward receipts, without game imports."""
from __future__ import division
import copy
import datetime
import re

try:
    integer_types = (int, long)
    string_types = (basestring,)
    text_type = unicode
except NameError:
    integer_types = (int,)
    string_types = (str,)
    text_type = str


def exact_amount(value):
    if isinstance(value, bool) or not isinstance(value, integer_types):
        return None
    return value if abs(value) <= 9007199254740991 else None


def safe_text(value, limit=180):
    if not isinstance(value, string_types):
        return ""
    if not isinstance(value, text_type):
        value = value.decode("utf-8", "replace")
    return re.sub(r"<[^>]*>", "", value).replace("\x00", "").strip()[:limit]


def message_time(message, now):
    for field in ("sentTime", "createdAt"):
        value = getattr(message, field, None)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and 946684800 <= value < 4102444800:
            return datetime.datetime.utcfromtimestamp(value).strftime("%Y-%m-%dT%H:%M:%SZ")
    return now


REWARD_KINDS = {
    "tokenQuests": u"Misi\u00f3n / recompensa",
    "potapovQuestBonus": u"Misi\u00f3n de campa\u00f1a",
    "personalMission3Quest": u"Misi\u00f3n de campa\u00f1a",
    "personalMission4Quest": u"Misi\u00f3n de campa\u00f1a",
    "hangarQuests": u"Misi\u00f3n adicional",
    "rankedQuests": u"Misi\u00f3n de clasificaci\u00f3n",
    "royaleQuests": u"Misi\u00f3n de evento",
    "battlePassReward": u"Recompensa del pase de batalla",
    "piggyBankSmashed": u"Reserva de cr\u00e9ditos",
    "invoiceReceived": u"Abono / retirada de cr\u00e9ditos",
}


def reward_receipt(message, kind, now, resolve_name=None, invoice_amount=None):
    """Whitelist actual credit fields; never infer amounts from quest definitions."""
    if kind != "battleResults" and kind not in REWARD_KINDS:
        return None
    data = getattr(message, "data", None)
    message_id = getattr(message, "messageId", None)
    if not isinstance(data, dict) or isinstance(message_id, bool) or message_id in (None, "", 0):
        return None
    battle_id = data.get("arenaUniqueID")
    if isinstance(battle_id, bool) or not isinstance(battle_id, integer_types + string_types):
        battle_id = None
    else:
        battle_id = text_type(battle_id)
    parts = []
    detailed = data.get("detailedRewards")
    if isinstance(detailed, dict):
        for quest_id, reward in sorted(detailed.items(), key=lambda item: text_type(item[0]))[:256]:
            if not isinstance(quest_id, string_types + integer_types) or not isinstance(reward, dict):
                continue
            amount = exact_amount(reward.get("credits"))
            if amount is None or amount == 0:
                continue
            identity = safe_text(text_type(quest_id))
            name = safe_text(resolve_name(identity)) if resolve_name is not None else ""
            parts.append({"quest_id": identity, "title": name or u"Misi\u00f3n " + identity,
                          "credits": amount, "name_resolved": bool(name)})
    amount = sum(part["credits"] for part in parts) if parts else None
    if kind == "invoiceReceived":
        # Adapter checks INVOICE_ASSET.CREDITS/DATA before supplying this delta.
        amount = exact_amount(invoice_amount)
    elif kind != "battleResults" and amount is None:
        amount = exact_amount(data.get("credits"))
    if kind == "battleResults" and not parts:
        return None
    if amount is None or amount == 0:
        return None
    return {"id": kind + ":" + text_type(message_id), "kind": kind,
            "occurred_at": message_time(message, now), "battle_id": battle_id,
            "credits": amount, "included_in_battle": kind == "battleResults",
            "title": REWARD_KINDS.get(kind, u"Misiones de la partida"), "parts": parts}


class WalletBook(object):
    def __init__(self, data=None):
        self.data = copy.deepcopy(data) if data is not None else {"schema": 1, "accounts": {}}
        if not isinstance(self.data, dict) or self.data.get("schema") != 1 or not isinstance(self.data.get("accounts"), dict):
            raise ValueError("invalid wallet document")
        for account in self.data["accounts"].values():
            if not isinstance(account, dict) or not isinstance(account.get("receipts", {}), dict):
                raise ValueError("invalid wallet account")
            for field in ("baseline", "balance"):
                if account.get(field) is not None and exact_amount(account[field]) is None:
                    raise ValueError("invalid saved wallet balance")

    def _account(self, region, account_id):
        key = region + ":" + str(account_id)
        return self.data["accounts"].setdefault(key, {"baseline": None, "balance": None,
                  "started_at": None, "observed_at": None, "receipts": {}})

    def observe(self, region, account_id, balance, now):
        if exact_amount(balance) is None or balance < 0:
            return False
        account = self._account(region, account_id)
        changed = account["baseline"] is None or account["balance"] != balance
        if account["baseline"] is None:
            account["baseline"] = balance
            account["started_at"] = now
        if changed:
            account["balance"] = balance
            account["observed_at"] = now
        return changed

    def upsert_receipt(self, region, account_id, receipt):
        account = self._account(region, account_id)
        old = account["receipts"].get(receipt["id"])
        if old == receipt:
            return False
        account["receipts"][receipt["id"]] = copy.deepcopy(receipt)
        return True

    def receipts(self, region, account_id):
        return copy.deepcopy(list(self._account(region, account_id)["receipts"].values()))

    def reconciliation(self, region, account_id, ledger, live_balance, period=None):
        account = self._account(region, account_id)
        baseline = account["baseline"]
        cutoff = account["started_at"]
        if period is not None and period.get("since_utc") is not None:
            baseline = period.get("baseline")
            cutoff = period["since_utc"]
        if baseline is None or live_balance is None:
            return {"ready": False, "baseline": baseline, "balance": live_balance,
                    "started_at": cutoff}
        battle_net = ledger.summary(region, account_id, since_utc=cutoff)["net_credits"]
        receipts = self.receipts(region, account_id)
        if period is not None:
            from .history import receipt_visible
            period = dict(period)
            period["excluded_receipts"] = frozenset(period.get("excluded_receipts", []))
        # Explicit battle + quest IDs identify the same award even if the server
        # repeats it through two message types. Client sequence IDs are not used.
        included = set((r.get("battle_id"), p["quest_id"]) for r in receipts
                       if r.get("included_in_battle") and r.get("battle_id")
                       for p in r.get("parts", []))
        external = 0
        for receipt in receipts:
            if period is not None:
                if not receipt_visible(receipt, period):
                    continue
            if receipt["occurred_at"] < cutoff or receipt.get("included_in_battle"):
                continue
            parts = receipt.get("parts", [])
            if parts:
                external += sum(p["credits"] for p in parts if not receipt.get("battle_id") or
                                (receipt["battle_id"], p["quest_id"]) not in included)
            else:
                external += receipt["credits"]
        change = live_balance - baseline
        return {"ready": True, "baseline": baseline, "balance": live_balance,
                "started_at": cutoff, "change": change, "battle_net": battle_net,
                "external_credits": external, "unclassified": change - battle_net - external,
                "reconciled_balance": live_balance}
