"""Buggy version: a shopping cart helper that leaks items between carts."""


def add_item(item, cart=[]):  # BUG: default list is shared across calls
    cart.append(item)
    return cart
