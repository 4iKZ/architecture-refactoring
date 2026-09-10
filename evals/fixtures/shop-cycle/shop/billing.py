"""Payment gateway client used by orders (demo only)."""

from shop import db
from shop import orders

GATEWAY_FEE = 0.02


def charge(order_id, amount):
    order = orders.get_order(order_id)
    result = _send_to_gateway(order_id, amount)
    if result["ok"]:
        order["status"] = "paid"
        order["paid_amount"] = amount
        orders.record_payment(order_id, amount)
    return result


def _send_to_gateway(order_id, amount):
    return {"ok": True, "charged": amount * (1 + GATEWAY_FEE)}


def calculate_total(total):
    # Pricing rule lives here too, with a slightly different boundary.
    if total > 100:
        return total * 0.9
    return total

# pass gateway fee to total
