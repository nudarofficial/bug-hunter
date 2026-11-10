'use strict';

// Buggy version: sums item prices fetched asynchronously.
async function totalPrice(ids, fetchItem) {
  let total = 0;
  // BUG: forEach does not await the async callback, so `return total`
  // runs before any price has been added.
  ids.forEach(async (id) => {
    const item = await fetchItem(id);
    total += item.priceCents;
  });
  return total;
}

module.exports = { totalPrice };
