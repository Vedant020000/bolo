"""Demo tests for the bolo video.

Pass by default. Set BOLO_DEMO_FAIL=1 to make one test fail on purpose,
so the commentary has something dramatic to say.
"""

import os
import unittest

from calc import add, mul, sub


class CalcTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)

    def test_sub(self):
        self.assertEqual(sub(5, 2), 3)

    def test_mul(self):
        self.assertEqual(mul(3, 4), 12)

    def test_mul_edge(self):
        expected = 13 if os.environ.get("BOLO_DEMO_FAIL") else 12
        self.assertEqual(mul(3, 4), expected)


if __name__ == "__main__":
    unittest.main()
