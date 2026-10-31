"""Package entry point smoke test — `python -m matchzerobaran` must work."""

from __future__ import annotations

import base  # noqa: F401
import unittest

from matchzerobaran.__main__ import main


class MainTest(unittest.TestCase):
    def test_no_args_prints_help(self):
        self.assertEqual(main([]), 0)

    def test_ingest_then_recommend(self):
        self.assertEqual(main(["ingest", "--data", str(base.DATA)]), 0)
        self.assertEqual(main(["recommend", "--customer", "C002", "-k", "2", "--raw"]), 0)


if __name__ == "__main__":
    unittest.main()