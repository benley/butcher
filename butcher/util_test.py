"""Unit tests for utility functions."""

import unittest

from butcher import util


class TestUtils(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testFlatten(self):
        """Verify that flatten() handles variously-nested iterables."""

        self.assertListEqual(
            list(util.flatten(["one", "two", ["three", "four"], "five"])),
            ["one", "two", "three", "four", "five"])

        self.assertListEqual(
            list(util.flatten(["a", "b", "c", "d", "e"])),
            ["a", "b", "c", "d", "e"])

        self.assertListEqual(
            list(util.flatten((["a", "b"], ["c", "d", ("e", "f"), "g"]))),
            ["a", "b", "c", "d", "e", "f", "g"])

        self.assertListEqual(
            list(util.flatten(["a", ["b", ["c", ["d", ["e", ["f", ["g"]]]]]]])
                 ),
            ["a", "b", "c", "d", "e", "f", "g"])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUtils)
    unittest.TextTestRunner(verbosity=2).run(suite)
