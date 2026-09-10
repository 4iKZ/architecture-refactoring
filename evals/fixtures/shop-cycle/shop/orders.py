"""Order lifecycle for the toy shop."""

from shop import billing
from shop import db, notifier

CATALOG = {
    "widget": {"price": 25.0, "name": "Widget"},
    "gadget": {"price": 80.0, "name": "Gadget"},
    "gizmo": {"price": 140.0, "name": "Gizmo"},
}


def create_order(order_id, sku, qty):
    item = CATALOG[sku]
    total = item["price"] * qty
    db.ORDERS[order_id] = {
        "id": order_id,
        "sku": sku,
        "qty": qty,
        "total": total,
        "status": "new",
        "paid_amount": 0.0,
    }
    return db.ORDERS[order_id]


def get_order(order_id):
    return db.ORDERS[order_id]


def mark_paid(order_id, amount):
    """Official state transition for a paid order."""
    order = db.ORDERS[order_id]
    if order["status"] == "paid":
        raise ValueError("order already paid")
    order["status"] = "paid"
    order["paid_amount"] = amount
    db.PAYMENTS.append({"order_id": order_id, "amount": amount})


def record_payment(order_id, amount):
    db.PAYMENTS.append({"order_id": order_id, "amount": amount})


def checkout(order_id):
    order = get_order(order_id)
    if order["status"] != "new":
        raise ValueError("order not open")
    total = apply_discount(order["total"])
    result = billing.charge(order_id, total)
    if result["ok"]:
        notifier.send_confirmation(order)
    return result


def apply_discount(total):
    if total >= 100:
        return total * 0.9
    return total

# add discount rule

# fix rounding
