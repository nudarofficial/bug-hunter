# JavaScript: async callback inside forEach

## Bug report (input)

> The checkout total is always 0, but the item service logs show every price being fetched.

## Bug Hunter report (output)

**Root cause:** in [buggy.js](buggy.js), `Array.prototype.forEach` calls the `async` callback and throws away the returned promise. `totalPrice` returns `total` before any `await fetchItem(...)` resolves. The prices are added later, after the caller already has `0`. That is why the logs show successful fetches.

**Status:** Confirmed. Reproduced by `buggy version returns before prices are added` in [test_example.js](test_example.js).

**Severity:** High. Wrong result on the main checkout path.

**Fix** ([fixed.js](fixed.js)):

```diff
-  let total = 0;
-  ids.forEach(async (id) => {
-    const item = await fetchItem(id);
-    total += item.priceCents;
-  });
-  return total;
+  const items = await Promise.all(ids.map((id) => fetchItem(id)));
+  return items.reduce((sum, item) => sum + item.priceCents, 0);
```

**Trade-off:** `Promise.all` fetches the items concurrently. If the item service is rate-limited, use a sequential `for (const id of ids) { ... await ... }` loop instead.

**Regression review:**
- An empty list still returns `0`.
- A failed fetch now rejects the returned promise. The old code raised an unhandled rejection and returned a wrong total.
- Callers must already `await` the function, since it was `async` before the fix too.

**Tests:** `node examples/javascript-async-foreach/test_example.js` (needs Node.js 18 or later for `node:test`)
