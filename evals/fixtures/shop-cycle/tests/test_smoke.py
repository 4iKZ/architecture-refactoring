import unittest

from shop import db, notifier, orders


class SmokeTest(unittest.TestCase):
    def setUp(self):
        db.reset()

    def test_checkout_marks_paid(self):
        orders.create_order("o-1", "widget", 1)
        orders.checkout("o-1")
        self.assertEqual(db.ORDERS["o-1"]["status"], "paid")

    def test_discount_over_100(self):
        self.assertEqual(orders.apply_discount(200), 180.0)

    def test_notifier_formats_paid_order(self):
        orders.create_order("o-2", "gadget", 1)
        orders.checkout("o-2")
        text = notifier.compose_confirmation(db.ORDERS["o-2"])
        self.assertIn("Gadget", text)
        self.assertIn("received", text.lower())


if __name__ == "__main__":
    unittest.main()
