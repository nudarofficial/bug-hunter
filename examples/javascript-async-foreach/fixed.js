'use strict';

// Fixed version: wait for every fetch before summing.
async function totalPrice(ids, fetchItem) {
  const items = await Promise.all(ids.map((id) => fetchItem(id)));
  return items.reduce((sum, item) => sum + item.priceCents, 0);
}

module.exports = { totalPrice };
