"""Warehouse operations (the intended stock owner)."""

from inv import db


def receive(sku, qty):
    row = db.STOCK[sku]
    row["on_hand"] += qty
    db.LEDGER.append(("receive", sku, qty))
    return row["on_hand"]


def ship(sku, qty):
    row = db.STOCK[sku]
    if row["on_hand"] - row["reserved"] < qty:
        raise ValueError("not enough stock")
    row["on_hand"] -= qty
    db.LEDGER.append(("ship", sku, qty))
    return row["on_hand"]


def available(sku):
    row = db.STOCK[sku]
    return row["on_hand"] - row["reserved"]
