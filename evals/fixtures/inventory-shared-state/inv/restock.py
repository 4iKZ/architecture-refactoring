"""Bulk restock helper (nightly job)."""

from inv import db


def apply_restock(plan):
    for sku, qty in plan.items():
        row = db.STOCK[sku]
        row["on_hand"] += qty
        db.LEDGER.append(("restock", sku, qty))
    return dict(plan)


def current_level(sku):
    return db.STOCK[sku]["on_hand"]
