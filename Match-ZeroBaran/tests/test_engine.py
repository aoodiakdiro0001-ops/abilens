"""Math layer: TF-IDF substitutes + market-basket complements."""

from __future__ import annotations

import base  # noqa: F401  (must run first: sets the environment)

import unittest

from matchzerobaran.engine import (
    AFFINITY,
    LIFT_CLIP,
    MIN_CO_OCCURRENCE,
    MatchEngine,
    category_affinity,
    tokenize,
)
from matchzerobaran.ingest import load_events, load_orders, load_products

PRODUCTS = load_products(base.DATA / "products.csv")
ORDERS = load_orders(base.DATA / "orders.csv")
EVENTS = load_events(base.DATA / "events.csv")


class EngineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng = MatchEngine(PRODUCTS, ORDERS, EVENTS)

    def test_sources_loaded(self):
        self.assertEqual(len(PRODUCTS), 12)
        self.assertEqual(len(ORDERS), 20)
        self.assertTrue(EVENTS)

    def test_tfidf_backend(self):
        try:
            import sklearn  # noqa: F401

            self.assertEqual(self.eng.index.kind, "sklearn", "sklearn installed but not used")
        except ImportError:
            self.assertEqual(self.eng.index.kind, "numpy")

    def test_substitutes_are_similar(self):
        rows = self.eng.similar("P001", k=3)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(p["id"] != "P001" for p, _, _ in rows))
        self.assertTrue(all(0 < s <= 1.0 + 1e-6 for _, s, _ in rows))
        # the closest neighbour of the DSLR kit must be a camera-adjacent item
        self.assertIn(rows[0][0]["id"], {"P002", "P003", "P004", "P005"})

    def test_lift_marks_real_baskets(self):
        self.assertGreaterEqual(self.eng.pair_counts[("P001", "P002")], MIN_CO_OCCURRENCE)
        self.assertGreaterEqual(self.eng.lift("P001", "P002"), 1.0)
        self.assertLessEqual(self.eng.lift("P001", "P002"), LIFT_CLIP)
        # never bought together → no signal
        self.assertEqual(self.eng.lift("P001", "P012"), 0.0)
        self.assertEqual(self.eng.lift("P001", "P001"), 0.0)

    def test_complements_exclude_self_and_label_reason(self):
        rows = self.eng.complements("P001", k=3)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(p["id"] != "P001" for p, _, _ in rows))
        self.assertTrue(all(r in {"basket", "affinity", "popular"} for _, _, r in rows))
        # camera body cross-sells to a camera accessory that really co-occurred
        self.assertEqual(rows[0][2], "basket")
        self.assertIn(rows[0][0]["category"], {"lenses", "bags"})

    def test_pair_table_is_sorted(self):
        table = self.eng.pair_table(10)
        lifts = [r[2] for r in table]
        self.assertEqual(lifts, sorted(lifts, reverse=True))
        self.assertTrue(table)
        self.assertGreaterEqual(table[0][2], 1.0)

    def test_customer_signals(self):
        bought, weights = self.eng.customer_signals("C001")
        self.assertIn("P001", bought)
        self.assertIn("P009", bought)
        self.assertGreater(weights.get("P009", 0), weights.get("P008", 0))  # cart > view
        empty, empty_w = self.eng.customer_signals("NOBODY")
        self.assertFalse(empty)
        self.assertFalse(empty_w)

    def test_affinity_table(self):
        pair = frozenset(("cameras", "lenses"))
        self.assertIn(pair, AFFINITY)
        self.assertEqual(category_affinity(PRODUCTS[0], PRODUCTS[1]), AFFINITY[pair])
        # shared tag fallback
        self.assertGreater(category_affinity(PRODUCTS[0], PRODUCTS[3]), 0.5)

    def test_tokenize_handles_arabic_and_latin(self):
        self.assertEqual(tokenize("Camera 24MP"), ["camera", "24mp"])
        self.assertTrue(tokenize("كاميرا احترافية"))


if __name__ == "__main__":
    unittest.main()