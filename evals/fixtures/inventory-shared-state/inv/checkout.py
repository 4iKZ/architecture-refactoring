"""Checkout flow that reserves stock."""

from inv import db
from inv.warehouse import available


def reserve(sku, qty):
    row = db.STOCK[sku]
    if row["on_hand"] - row["reserved"] < qty:
        raise ValueError("not enough stock")
    row["reserved"] += qty
    return row["reserved"]


def release(sku, qty):
    row = db.STOCK[sku]
    row["reserved"] -= qty
    return row["reserved"]


def reservation_count(sku):
    return db.STOCK[sku]["reserved"]
