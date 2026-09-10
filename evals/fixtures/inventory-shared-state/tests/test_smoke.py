import unittest

from inv import checkout, db, restock, warehouse


class StockTest(unittest.TestCase):
    def setUp(self):
        db.reset()

    def test_receive_adds_stock(self):
        warehouse.receive("widget", 2)
        self.assertEqual(db.STOCK["widget"]["on_hand"], 12)

    def test_reserve_math(self):
        checkout.reserve("gadget", 2)
        self.assertEqual(checkout.reservation_count("gadget"), 2)

    def test_restock_adds_stock(self):
        restock.apply_restock({"gizmo": 3})
        self.assertEqual(db.STOCK["gizmo"]["on_hand"], 5)


if __name__ == "__main__":
    unittest.main()
