'use strict';

// Regression test. Run with: node examples/javascript-async-foreach/test_example.js
const test = require('node:test');
const assert = require('node:assert/strict');
const buggy = require('./buggy.js');
const fixed = require('./fixed.js');

const PRICES = { a: 250, b: 1000, c: 49 };

function fakeFetchItem(id) {
  // Resolve on a later timer tick to behave like real I/O.
  return new Promise((resolve) => setTimeout(() => resolve({ id, priceCents: PRICES[id] }), 5));
}

test('buggy version returns before prices are added', async () => {
  assert.equal(await buggy.totalPrice(['a', 'b', 'c'], fakeFetchItem), 0);
  // Let the stray callbacks finish so they do not leak into other tests.
  await new Promise((resolve) => setTimeout(resolve, 20));
});

test('fixed version sums all prices', async () => {
  assert.equal(await fixed.totalPrice(['a', 'b', 'c'], fakeFetchItem), 1299);
});

test('fixed version handles an empty list', async () => {
  assert.equal(await fixed.totalPrice([], fakeFetchItem), 0);
});

test('fixed version propagates fetch errors instead of hiding them', async () => {
  const failing = async () => { throw new Error('item service unavailable'); };
  await assert.rejects(fixed.totalPrice(['a'], failing), /item service unavailable/);
});
