"""In-memory stock tables for the warehouse demo."""

STOCK = {}
LEDGER = []


def reset():
    STOCK.clear()
    LEDGER.clear()
    for sku, qty in (("widget", 10), ("gadget", 4), ("gizmo", 2)):
        STOCK[sku] = {"sku": sku, "on_hand": qty, "reserved": 0}
