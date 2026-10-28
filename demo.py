# -*- coding: utf-8 -*-
"""Demostracion local con datos ficticios; no conecta con World of Tanks."""
from __future__ import print_function

import json

from core import EconomyLedger


def main():
    ledger = EconomyLedger()
    samples = [(80000, 8000, 12000, 9000),
               (62000, 10000, 14000, 8000),
               (45000, 18000, 20000, 15000)]
    for index, values in enumerate(samples, 1):
        gross, repair, ammo, consumables = values
        ledger.upsert_result({
            "region": "NA", "account_id": "cuenta-de-ejemplo",
            "battle_id": "ejemplo-%s" % index,
            "occurred_at": "2026-10-17T18:0%s:00Z" % index,
            "status": "final",
            "credits": {"gross": gross, "expenses": {
                "repair": repair, "ammo": ammo,
                "consumables": consumables, "other": 0}},
        })
    goal = {"region": "NA", "account_id": "cuenta-de-ejemplo",
            "mode": "balance", "target": 3000000,
            "since_utc": "2026-10-17T05:00:00Z"}
    print("DEMOSTRACION CON DATOS FICTICIOS")
    print(json.dumps({
        "resumen": ledger.summary("NA", "cuenta-de-ejemplo"),
        "meta": ledger.goal_status(goal, external_balance=2473000),
    }, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
