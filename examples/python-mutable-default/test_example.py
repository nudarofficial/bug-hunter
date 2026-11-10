"""Regression test: proves the bug exists in buggy.py and is gone in fixed.py."""

import importlib.util
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(f"pmd_{name}", HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MutableDefaultTest(unittest.TestCase):
    def test_buggy_version_leaks_state_between_calls(self):
        buggy = load("buggy")
        buggy.add_item("apple")
        self.assertEqual(buggy.add_item("pear"), ["apple", "pear"])

    def test_fixed_version_isolates_calls(self):
        fixed = load("fixed")
        self.assertEqual(fixed.add_item("apple"), ["apple"])
        self.assertEqual(fixed.add_item("pear"), ["pear"])

    def test_fixed_version_still_mutates_caller_supplied_cart(self):
        fixed = load("fixed")
        cart = ["milk"]
        result = fixed.add_item("bread", cart)
        self.assertIs(result, cart)
        self.assertEqual(cart, ["milk", "bread"])


if __name__ == "__main__":
    unittest.main()
