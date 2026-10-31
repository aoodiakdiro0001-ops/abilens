"""Similarity & market-basket core (the math layer).

* TF-IDF + cosine similarity  -> **substitutes** ("customers who viewed X also viewed Y")
* Market-basket lift          -> **complements**  ("X is bought together with Y")
* Curated category affinity   -> graceful fallback when basket history is thin

scikit-learn is used when installed; otherwise a numpy implementation takes
over so the engine still runs (the project claims "100% free", not "100% cloud").
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from itertools import combinations
from typing import Any, Iterable

import numpy as np

# --------------------------------------------------------------------------- #
# tunables
# --------------------------------------------------------------------------- #
MIN_CO_OCCURRENCE = 2     # pairs below this are treated as noise
LIFT_CLIP = 6.0           # lift scores are clipped to keep blends stable
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[؀-ۿ]+")

# cross-category complementarity, used when basket data is sparse
AFFINITY: dict[frozenset, float] = {
    frozenset(("cameras", "lenses")): 1.00,
    frozenset(("cameras", "bags")): 0.95,
    frozenset(("cameras", "storage")): 0.95,
    frozenset(("laptops", "desk")): 0.90,
    frozenset(("laptops", "audio")): 0.75,
    frozenset(("laptops", "power")): 0.85,
    frozenset(("audio", "power")): 0.70,
    frozenset(("coffee", "drinkware")): 0.95,
    frozenset(("fragrance", "drinkware")): 0.30,
    frozenset(("lenses", "storage")): 0.60,
}


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def product_doc(p: dict[str, Any]) -> str:
    """Document fed to TF-IDF — name & tags repeated to weight them higher."""
    tags = str(p.get("tags") or "").replace(",", " ")
    name = str(p.get("name") or "")
    return " ".join(
        [
            name,
            name,
            str(p.get("category") or ""),
            tags,
            tags,
            str(p.get("description") or ""),
        ]
    )


def category_affinity(a: dict[str, Any], b: dict[str, Any]) -> float:
    ca, cb = str(a.get("category") or ""), str(b.get("category") or "")
    if ca and ca == cb:
        return 0.35  # same category = substitute, handled by similarity instead
    key = frozenset((ca, cb))
    if key in AFFINITY:
        return AFFINITY[key]
    ta = {t for t in tokenize(str(a.get("tags") or ""))}
    tb = {t for t in tokenize(str(b.get("tags") or ""))}
    if ta & tb:
        return 0.90
    return 0.40


# --------------------------------------------------------------------------- #
# TF-IDF index
# --------------------------------------------------------------------------- #
class TfidfIndex:
    """Dense-numpy by default, scikit-learn sparse when available."""

    def __init__(self, docs: Iterable[str]):
        self.docs = list(docs)
        self.kind = "numpy"
        self._M = None
        self._X = None
        if not self.docs:
            self._X = np.zeros((1, 1))
            return
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer

            vectorizer = TfidfVectorizer(
                tokenizer=tokenize,
                preprocessor=lambda s: s,
                token_pattern=None,
                ngram_range=(1, 2),
                lowercase=True,
                sublinear_tf=True,
            )
            self._M = vectorizer.fit_transform(self.docs)
            self.kind = "sklearn"
        except Exception:  # pragma: no cover - fallback path
            self._X = self._numpy_fit(self.docs)

    # numpy fallback ---------------------------------------------------------
    def _numpy_fit(self, docs: list[str]) -> np.ndarray:
        counts = [Counter(tokenize(d)) for d in docs]
        vocab: dict[str, int] = {}
        for c in counts:
            for term in c:
                vocab.setdefault(term, len(vocab))
        n = len(docs)
        df = Counter()
        for c in counts:
            for term in set(c):
                df[term] += 1
        X = np.zeros((n, max(1, len(vocab))), dtype=float)
        for i, c in enumerate(counts):
            for term, tf in c.items():
                j = vocab[term]
                idf = math.log((1 + n) / (1 + df[term])) + 1.0
                X[i, j] = (1 + math.log(tf)) * idf
        norm = np.linalg.norm(X, axis=1, keepdims=True)
        norm[norm == 0] = 1.0
        return X / norm

    # queries ----------------------------------------------------------------
    def scores(self, i: int) -> np.ndarray:
        """Cosine similarity of row `i` against every row."""
        if self.kind == "sklearn" and self._M is not None:
            return np.asarray((self._M[i] @ self._M.T).todense()).ravel()
        return self._X[i] @ self._X.T

    def top(self, i: int, k: int, exclude: set[int] | None = None) -> list[tuple[int, float]]:
        s = self.scores(i)
        order = np.argsort(-s)
        out: list[tuple[int, float]] = []
        exclude = exclude or set()
        for j in order:
            j = int(j)
            if j == i or j in exclude:
                continue
            if s[j] <= 0:
                break
            out.append((j, round(float(s[j]), 4)))
            if len(out) >= k:
                break
        return out


# --------------------------------------------------------------------------- #
# engine
# --------------------------------------------------------------------------- #
class MatchEngine:
    """Fits products + orders once, then answers substitute/complement queries."""

    def __init__(
        self,
        products: list[dict[str, Any]],
        orders: list[dict[str, Any]] | None = None,
        events: list[dict[str, Any]] | None = None,
    ):
        self.products = [p for p in products if p.get("id")]
        self.orders = orders or []
        self.events = events or []
        self.by_id: dict[str, dict[str, Any]] = {p["id"]: p for p in self.products}
        self.index = TfidfIndex([product_doc(p) for p in self.products])
        self._pos = {p["id"]: i for i, p in enumerate(self.products)}
        self._build_baskets()
        self._lift_cache: dict[tuple[str, str], float] = {}

    # -- baskets --------------------------------------------------------------
    def _build_baskets(self) -> None:
        self.item_counts: Counter = Counter()
        self.pair_counts: Counter = Counter()
        self.revenue: Counter = Counter()
        for order in self.orders:
            ids = sorted(
                {
                    it.get("product_id")
                    for it in order.get("items", [])
                    if it.get("product_id") in self.by_id
                }
            )
            for pid in ids:
                self.item_counts[pid] += 1
            for a, b in combinations(ids, 2):
                self.pair_counts[(a, b)] += 1
            for it in order.get("items", []):
                pid = it.get("product_id")
                if pid in self.by_id:
                    self.revenue[pid] += float(it.get("qty", 1)) * float(it.get("price", 0) or 0)
        self.n_orders = max(1, len(self.orders))

    # -- lift -----------------------------------------------------------------
    def lift(self, a: str, b: str) -> float:
        if a == b:
            return 0.0
        key = tuple(sorted((a, b)))
        if key in self._lift_cache:
            return self._lift_cache[key]
        value = 0.0
        if self.pair_counts.get(key, 0) >= MIN_CO_OCCURRENCE:
            pa = self.item_counts[a] / self.n_orders
            pb = self.item_counts[b] / self.n_orders
            pab = self.pair_counts[key] / self.n_orders
            if pa > 0 and pb > 0:
                value = pab / (pa * pb)
        value = min(LIFT_CLIP, value)
        self._lift_cache[key] = value
        return value

    def popularity(self, pid: str) -> float:
        if not self.item_counts:
            return 0.0
        return self.item_counts[pid] / max(self.item_counts.values())

    # -- queries ---------------------------------------------------------------
    def similar(self, pid: str, k: int = 3) -> list[tuple[dict[str, Any], float, str]]:
        """Substitutes: cosine neighbours of the product document."""
        i = self._pos.get(pid)
        if i is None:
            return []
        out = []
        for j, score in self.index.top(i, k):
            p = self.products[j]
            out.append((p, score, "similar"))
        return out

    def complements(self, pid: str, k: int = 3) -> list[tuple[dict[str, Any], float, str]]:
        """Complements: basket lift blended with category affinity + popularity."""
        base = self.by_id.get(pid)
        if not base:
            return []
        scored = []
        for p in self.products:
            if p["id"] == pid:
                continue
            lift = self.lift(pid, p["id"]) / LIFT_CLIP
            aff = category_affinity(base, p)
            pop = self.popularity(p["id"])
            has_basket = self.pair_counts.get(tuple(sorted((pid, p["id"]))), 0) >= MIN_CO_OCCURRENCE
            # one scale for everyone: lift dominates, affinity & popularity fill in.
            # Pairs without co-purchase evidence keep the same scale but with a
            # confidence haircut, so real baskets are never ranked below guesses.
            score = 0.55 * lift + 0.30 * aff + 0.15 * pop
            if not has_basket:
                score *= 0.85
            reason = "basket" if has_basket else ("affinity" if aff >= 0.6 else "popular")
            scored.append((p, round(score, 4), reason))
        scored.sort(key=lambda t: -t[1])
        return scored[:k]

    def pair_table(self, top: int = 20) -> list[tuple[str, str, float, int]]:
        """(a, b, lift, times-bought-together) sorted by lift — dashboard fodder."""
        rows = []
        for (a, b), c in self.pair_counts.items():
            if a not in self.by_id or b not in self.by_id:
                continue
            rows.append((a, b, round(self.lift(a, b), 3), c))
        rows.sort(key=lambda r: (-r[2], -r[3]))
        return rows[:top]

    # -- customer level ---------------------------------------------------------
    def customer_signals(self, customer_id: str) -> tuple[Counter, dict[str, float]]:
        """Returns (purchased product ids, {product_id: behaviour weight})."""
        bought: Counter = Counter()
        for order in self.orders:
            if order.get("customer_id") != customer_id:
                continue
            for it in order.get("items", []):
                pid = it.get("product_id")
                if pid in self.by_id:
                    bought[pid] += int(it.get("qty", 1) or 1)
        weights: dict[str, float] = defaultdict(float)
        weight_of = {"view": 0.3, "cart": 0.7, "purchase": 1.0}
        for ev in self.events:
            if ev.get("customer_id") != customer_id:
                continue
            pid = ev.get("product_id")
            if pid in self.by_id:
                weights[pid] += weight_of.get(ev.get("type", "view"), 0.3)
        return bought, dict(weights)