"""End-to-end: CSV -> store -> recommendations -> digest, plus the CLI."""

from __future__ import annotations

import base  # noqa: F401  (must run first)

import json
import unittest
from pathlib import Path

from matchzerobaran import config
from matchzerobaran.cli import main
from matchzerobaran.delivery import build_digest, telegram_send
from matchzerobaran.engine import MatchEngine
from matchzerobaran.ingest import export_recommendations, ingest, load_all
from matchzerobaran.recommend import (
    recommend_for_customer,
    recommend_for_product,
    refresh,
)
from matchzerobaran.store import Store, open_store


class IngestStoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = open_store()
        cls.counts = ingest(cls.store, base.DATA)

    def test_ingest_counts(self):
        self.assertEqual(self.counts["products"], 12)
        self.assertEqual(self.counts["customers"], 8)
        self.assertEqual(self.counts["orders"], 20)
        self.assertEqual(self.counts["events"], 22)

    def test_orders_grouped_with_totals(self):
        data = load_all(self.store)
        order = next(o for o in data["orders"] if o["id"] == "O1001")
        self.assertEqual(len(order["items"]), 2)
        self.assertAlmostEqual(order["total"], 870.0)

    def test_store_round_trip(self):
        tmp = Store(Path(base.__file__).parent / "_tmp_store")
        try:
            self.assertEqual(tmp.save("products", [{"id": "X1", "name": "n"}]), 1)
            tmp.upsert("products", "id", [{"id": "X1", "name": "renamed"}])
            rows = tmp.load("products")
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["name"], "renamed")
            self.assertEqual(tmp.load("missing_table"), [])
        finally:
            import shutil

            shutil.rmtree(tmp.root, ignore_errors=True)

    def test_supabase_is_optional(self):
        self.assertFalse(self.store.sync("products"))  # no URL configured

    def test_export_recommendations(self):
        rows = [{"customer_id": "C001", "product_id": "P002", "score": 0.9}]
        path = export_recommendations(self.store, rows)
        self.assertTrue(path.exists())
        self.assertEqual(json.loads(path.read_text(encoding="utf-8")), rows)


class RecommendTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = open_store()
        ingest(cls.store, base.DATA)
        data = load_all(cls.store)
        cls.eng = MatchEngine(data["products"], data["orders"], data["events"])
        cls.bought = {
            it["product_id"]
            for o in data["orders"]
            if o["customer_id"] == "C001"
            for it in o["items"]
        }

    def test_customer_gets_k_fresh_items(self):
        rows = recommend_for_customer(self.store, eng=self.eng, customer_id="C001", k=3)
        self.assertEqual(len(rows), 3)
        self.assertFalse({r["product_id"] for r in rows} & self.bought, "already bought items leaked in")
        for r in rows:
            self.assertTrue(r["name"])
            self.assertTrue(r["pitch"], "pitch must always be produced (AI or template)")
            self.assertTrue(r["reason_text"])
            self.assertIn(r["reason"], {"basket", "affinity", "similar", "popular"})
            self.assertGreaterEqual(r["score"], 0)

    def test_pitches_are_arabic_by_default(self):
        rows = recommend_for_customer(self.store, eng=self.eng, customer_id="C001", k=3)
        for r in rows:
            self.assertRegex(r["pitch"], r"[؀-ۿ]", "expected an Arabic pitch")

    def test_cold_start_falls_back_to_popularity(self):
        rows = recommend_for_customer(self.store, eng=self.eng, customer_id="C-NEW", k=3)
        self.assertEqual(len(rows), 3)
        self.assertEqual([r["reason"] for r in rows], ["popular"] * 3)
        scores = [r["score"] for r in rows]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_product_cross_sell(self):
        rows = recommend_for_product(self.store, "P001", eng=self.eng, k=3)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r["product_id"] != "P001" for r in rows))
        # top cross-sell must carry real co-purchase evidence and fit the camera kit
        self.assertEqual(rows[0]["reason"], "basket")
        self.assertIn(rows[0]["category"], {"lenses", "bags"})

    def test_refresh_writes_matrix(self):
        info = refresh(self.store, k=3)
        self.assertEqual(info["customers"], 8)
        self.assertEqual(info["rows"], 24)
        self.assertTrue(Path(info["path"]).exists())

    def test_english_pitches(self):
        rows = recommend_for_customer(self.store, eng=self.eng, customer_id="C001", k=2, lang="en")
        for r in rows:
            self.assertNotRegex(r["pitch"], r"[؀-ۿ]")


class DeliveryTest(unittest.TestCase):
    def test_digest_carries_support_and_rights(self):
        store = open_store()
        rows = recommend_for_customer(store, customer_id="C001", k=3)
        digest = build_digest(rows, customer_name="أحمد")
        self.assertIn("Baran Avisat", digest)
        self.assertIn(config.SUPPORT_EMAIL, digest)
        self.assertIn("00905313263722" in digest or config.SUPPORT_PHONE in digest, [True])

    def test_telegram_is_silent_without_keys(self):
        self.assertFalse(telegram_send("hello"))

    def test_empty_digest(self):
        self.assertIn("لا توجد", build_digest([]))


class CliTest(unittest.TestCase):
    def test_status(self):
        self.assertEqual(main(["status"]), 0)

    def test_recommend_json(self):
        self.assertEqual(main(["recommend", "--customer", "C001", "-k", "2", "--json"]), 0)

    def test_report(self):
        self.assertEqual(main(["report"]), 0)

    def test_digest_command(self):
        self.assertEqual(main(["digest", "--customer", "C001", "-k", "2"]), 0)

    def test_version(self):
        with self.assertRaises(SystemExit) as ctx:
            main(["--version"])
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()