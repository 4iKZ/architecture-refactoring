"""Tiny in-memory store used by the demo app."""

ORDERS = {}
PAYMENTS = []


def reset():
    ORDERS.clear()
    PAYMENTS.clear()
