from shop import db, orders


def run():
    db.reset()
    orders.create_order("o-1", "gizmo", 1)
    result = orders.checkout("o-1")
    return result, db.ORDERS["o-1"]


if __name__ == "__main__":
    print(run())
