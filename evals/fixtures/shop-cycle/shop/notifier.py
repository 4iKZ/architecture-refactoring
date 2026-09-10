"""Order confirmation emails (plain text only)."""


def send_confirmation(order):
    return compose_confirmation(order)


def compose_confirmation(order):
    sku = order["sku"]
    q = order["qty"]
    st = order["status"]
    amt = order.get("paid_amount", 0.0)
    if sku == "widget":
        hdr = "Thanks for buying a Widget!"
    elif sku == "gadget":
        hdr = "Your Gadget is on its way."
    elif sku == "gizmo":
        hdr = "A fancy Gizmo for you."
    else:
        hdr = "Thanks for your order."
    if st == "paid":
        body = "We received %.2f." % amt
    elif st == "new":
        body = "Please complete payment."
    else:
        body = "Order status: " + str(st)
    return "%s\n%s\nItems: %d x %s\n" % (hdr, body, q, sku)
