# Worked Examples

## Contents

- [Example 1: Breaking an orders↔billing cycle (subsystem)](#example-1-breaking-an-ordersbilling-cycle)
- [Example 2: Assigning an owner for shared stock state (local)](#example-2-assigning-an-owner-for-shared-stock-state)
- [Example 3: When the evidence says leave it alone](#example-3-when-the-evidence-says-leave-it-alone)

## Example 1: Breaking an orders↔billing cycle

### Evidence

The demo app has an order pipeline and a payment gateway client.

```text
db ← orders → billing → orders     (import cycle)
```

- `orders.checkout()` calls `billing.charge()`.
- `billing.charge()` imports `orders` to read the order and writes order
  state directly: `order["status"] = "paid"`, `order["paid_amount"] = amount`.
- The discount rule exists twice with drifted boundaries:
  `orders.apply_discount` uses `>= 100`, `billing.calculate_total` uses `> 100`.
- `orders.mark_paid()` is the intended state transition but the checkout path
  never uses it, so its guard (`"already paid"`) is unreachable in practice.

### Diagnosis

The mechanism is **split ownership of the order lifecycle**. `billing` is a
volatile mechanism (gateway client) that has acquired two responsibilities it
should not own: deciding when an order becomes paid, and computing pricing.
The cycle is a symptom; moving the import would not remove the knowledge.

### Target boundary

- **orders** — owns the order lifecycle and its invariants. All paid-state
  transitions go through `mark_paid`.
- **billing** — an adapter around the volatile external mechanism. Its
  contract becomes `charge(order_id, amount) -> PaymentResult`; it knows
  nothing about order state.
- **pricing** — a single owner for discount rules (`apply_discount`).

### Migration

Step 1 — introduce the seam. Keep `billing` reach-back temporarily, but route
the state change through the owner:

```python
# billing.py — before
if result["ok"]:
    order["status"] = "paid"
    order["paid_amount"] = amount
    orders.record_payment(order_id, amount)
```

```python
# billing.py — after (temporary compatibility step)
if result["ok"]:
    orders.mark_paid(order_id, amount)   # still imports orders, but no direct writes
```

Step 2 — verify with the narrowest tests plus one end-to-end checkout.

Step 3 — invert the dependency. `billing` stops importing `orders` and stops
reading order state; it only reports the gateway result:

```python
# billing.py — final
def charge(order_id, amount):
    return _send_to_gateway(order_id, amount)
```

```python
# orders.py — checkout becomes the orchestrator
def checkout(order_id):
    order = get_order(order_id)
    if order["status"] != "new":
        raise ValueError("order not open")
    amount = apply_discount(order["total"])
    result = billing.charge(order_id, amount)
    if result["ok"]:
        mark_paid(order_id, amount)
        notifier.send_confirmation(order)
    return result
```

Step 4 — verify again; confirm the paid transition still executes exactly once
and the guard path is now reachable.

Step 5 — delete the duplicated pricing rule and the now-unused
`record_payment`; add the dependency direction as a check if tooling exists
(`orders → billing`, never the reverse).

### Verification

- Behavior: the fixture test suite passes; a checkout run produces the same
  externally observable output as the baseline.
- Architecture: `billing` no longer imports `orders` or `db`; a single owner
  writes order state; one discount rule remains.

### Trade-off

- Coupling removed: `billing → orders`, `billing → db`, duplicated pricing
  knowledge.
- Coupling introduced: `checkout` now explicitly sequences "charge, then mark
  paid" — the same application-level orchestration, in the module that already
  owned the flow.
- Why preferable: the volatile gateway adapter no longer knows the order
  lifecycle, so swapping providers cannot alter state transitions.

## Example 2: Assigning an owner for shared stock state

### Evidence

In a small inventory app, three modules write the same rows:

- `warehouse.receive/ship` adjust `on_hand`;
- `checkout.reserve/release` adjust `reserved` and re-implement the
  availability rule;
- `restock.apply_restock` adjusts `on_hand` and ignores reservations.

`checkout.release` can drive `reserved` negative because the invariant is
enforced nowhere.

### Diagnosis

No module is the authoritative owner of stock invariants. Reads look harmless;
the cost is that every stock rule change must be made in three places and can
drift.

### Target boundary

`warehouse` owns `on_hand` + `reserved` and exposes `reserve`, `release`,
`receive`, `ship`, `available`. Other modules request operations instead of
writing rows.

### Migration

1. Add `reserve`/`release` to `warehouse` (the owner, already importable).
2. Migrate one caller (`checkout.reserve`) and verify with its tests.
3. Migrate `checkout.release` and `restock`; verify after each.
4. Enforce: only `warehouse` writes stock fields (a code check if the project
   has one; otherwise reviewed convention).

This is a local change: no new module, no interface with a single
implementation, no folder reshuffle.

## Example 3: When the evidence says leave it alone

A user asks: "`notifier.py` is ugly — the naming is terrible and there is a big
if/elif chain. Restructure it properly."

Evidence gathered:

- the file has not changed in over a year (change history);
- no other module depends on its internals, and no defects point at it;
- there is no near-term requirement that would make it change.

Decision: recommend leaving the structure unchanged; if the naming really
bothers the team, do a cosmetic cleanup as a separate change, explicitly not
an architecture migration. "Ugly" is not a finding; low churn plus small blast
radius means the refactor buys little and risks behavior drift.

What would change the decision: the email provider becomes swappable, a second
channel (SMS/push) is planned, localization or templating requirements arrive,
or defects accumulate around message formatting. Those are change reasons —
and they would justify extracting a boundary then, not now.
