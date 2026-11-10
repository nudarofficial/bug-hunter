# Python: mutable default argument

## Bug report (input)

> Users see items from other people's carts. `add_item("pear")` on a fresh cart returns `["apple", "pear"]`.

## Bug Hunter report (output)

**Root cause:** `add_item` in [buggy.py](buggy.py) uses `cart=[]` as a default. Python evaluates default values once, when the function is defined, so every call that omits `cart` appends to the same list.

**Status:** Confirmed — reproduced by `test_buggy_version_leaks_state_between_calls` in [test_example.py](test_example.py).

**Severity:** High — wrong results on the common path, and data leaks between users.

**Fix** ([fixed.py](fixed.py)):

```diff
-def add_item(item, cart=[]):
+def add_item(item, cart=None):
+    if cart is None:
+        cart = []
     cart.append(item)
     return cart
```

**Regression review:** Callers that pass their own list still have it mutated in place and returned. That behavior is unchanged and covered by `test_fixed_version_still_mutates_caller_supplied_cart`.

**Tests:** `python examples/python-mutable-default/test_example.py`
