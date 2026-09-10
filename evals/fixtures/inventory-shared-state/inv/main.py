from inv import checkout, db, restock, warehouse


def run():
    db.reset()
    warehouse.receive("gadget", 2)
    checkout.reserve("gadget", 3)
    restock.apply_restock({"widget": 5})
    return dict(db.STOCK)


if __name__ == "__main__":
    print(run())
