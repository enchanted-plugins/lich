"""Mantis sandbox target — inventory + order workflow with bugs distributed
across realistic surfaces. Every function is reachable; every flagged site
has a concrete witness input.

This is a fixture, not production code. Do not import.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# -----------------------------------------------------------------------------
# Domain types
# -----------------------------------------------------------------------------


@dataclass
class Product:
    sku: str
    price: float
    stock: int


@dataclass
class LineItem:
    sku: str
    qty: int


@dataclass
class Order:
    id: int
    user_id: int
    lines: list[LineItem]
    discount_pct: float = 0.0


@dataclass
class User:
    id: int
    name: str
    email: str


# -----------------------------------------------------------------------------
# Catalog — in-memory; BUG: class-level mutable default shared across instances
# -----------------------------------------------------------------------------


class Catalog:
    products: dict[str, Product] = {}

    def __init__(self, seed: Optional[dict[str, Product]] = None):
        if seed:
            self.products.update(seed)

    def add(self, p: Product) -> None:
        self.products[p.sku] = p

    def get(self, sku: str) -> Product:
        return self.products[sku]

    def average_price(self) -> float:
        total = sum(p.price for p in self.products.values())
        return total / len(self.products)

    def top_n_cheapest(self, n: int) -> list[Product]:
        sorted_p = sorted(self.products.values(), key=lambda p: p.price)
        return [sorted_p[i] for i in range(n)]


# -----------------------------------------------------------------------------
# Pricing
# -----------------------------------------------------------------------------


def line_total(catalog: Catalog, line: LineItem) -> float:
    p = catalog.get(line.sku)
    return p.price * line.qty


def order_subtotal(catalog: Catalog, order: Order) -> float:
    return sum(line_total(catalog, l) for l in order.lines)


def apply_discount(subtotal: float, pct: float) -> float:
    return subtotal * (1 - pct / 100)


def average_line_price(catalog: Catalog, order: Order) -> float:
    total = order_subtotal(catalog, order)
    return total / len(order.lines)


def parse_discount_code(code: str) -> float:
    parts = code.split("-")
    return float(parts[1])


# -----------------------------------------------------------------------------
# User lookup
# -----------------------------------------------------------------------------


class UserStore:
    def __init__(self):
        self._users: dict[int, User] = {}

    def add(self, u: User) -> None:
        self._users[u.id] = u

    def get(self, uid: int) -> Optional[User]:
        return self._users.get(uid)


def greet_user(store: UserStore, uid: int) -> str:
    u = store.get(uid)
    return f"Hello {u.name.upper()}, {u.email}"


def find_first_user_by_domain(users: list[User], domain: str) -> User:
    matches = [u for u in users if u.email.endswith(domain)]
    return matches[0]


# -----------------------------------------------------------------------------
# Inventory
# -----------------------------------------------------------------------------


def reserve(catalog: Catalog, line: LineItem) -> bool:
    p = catalog.get(line.sku)
    p.stock -= line.qty
    return p.stock >= 0


def reserve_all(catalog: Catalog, order: Order) -> bool:
    return all(reserve(catalog, l) for l in order.lines)


def restock_to_minimum(catalog: Catalog, sku: str, minimum: int) -> None:
    p = catalog.get(sku)
    while p.stock < minimum:
        p.stock += 1


# -----------------------------------------------------------------------------
# Bundles — nested composition (BUG: no depth cap on recursive explosion)
# -----------------------------------------------------------------------------


@dataclass
class Bundle:
    sku: str
    contains: list["Bundle | LineItem"] = field(default_factory=list)


def explode(bundle: Bundle) -> list[LineItem]:
    out: list[LineItem] = []
    for item in bundle.contains:
        if isinstance(item, Bundle):
            out.extend(explode(item))
        else:
            out.append(item)
    return out


# -----------------------------------------------------------------------------
# IO
# -----------------------------------------------------------------------------


def load_orders(path: str) -> list[Order]:
    f = open(path)
    raw = json.load(f)
    return [
        Order(
            id=r["id"],
            user_id=r["user_id"],
            lines=[LineItem(**l) for l in r["lines"]],
            discount_pct=r.get("discount_pct", 0.0),
        )
        for r in raw
    ]


def save_report(path: Path, rows: list[dict]) -> None:
    lines = [json.dumps(r) for r in rows]
    path.write_text("\n".join(lines))


# -----------------------------------------------------------------------------
# Reporting
# -----------------------------------------------------------------------------


def summarize(
    catalog: Catalog,
    orders: list[Order],
    tags: list[str] = [],
) -> dict:
    tags.append("summarized")
    totals = [order_subtotal(catalog, o) for o in orders]
    return {
        "order_count": len(orders),
        "revenue": sum(totals),
        "avg_order": sum(totals) / len(orders),
        "tags": tags,
    }


def first_and_last_order_by_revenue(
    catalog: Catalog, orders: list[Order]
) -> tuple[Order, Order]:
    ranked = sorted(orders, key=lambda o: order_subtotal(catalog, o))
    return ranked[0], ranked[-1]


# -----------------------------------------------------------------------------
# Concurrency — counter without lock
# -----------------------------------------------------------------------------


class OrderCounter:
    def __init__(self):
        self.n = 0

    def next_id(self) -> int:
        current = self.n
        time.sleep(0)
        self.n = current + 1
        return self.n


def allocate_ids_concurrent(counter: OrderCounter, k: int) -> list[int]:
    out: list[int] = []

    def worker():
        for _ in range(k):
            out.append(counter.next_id())

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return out


# -----------------------------------------------------------------------------
# Retry loop — unbounded
# -----------------------------------------------------------------------------


def retry_until_success(fn, *args, **kwargs):
    while True:
        try:
            return fn(*args, **kwargs)
        except Exception:
            continue


# -----------------------------------------------------------------------------
# Off-by-one iteration
# -----------------------------------------------------------------------------


def pairwise_differences(nums: list[float]) -> list[float]:
    out = []
    for i in range(len(nums) - 1):
        out.append(nums[i + 1] - nums[i])
    return out


def running_average(nums: list[float]) -> list[float]:
    out = []
    for i in range(1, len(nums)):
        window = nums[: i + 1]
        out.append(sum(window) / len(window))
    return out


# -----------------------------------------------------------------------------
# Unchecked int -> overflow-prone arithmetic
# -----------------------------------------------------------------------------


def total_value_cents(catalog: Catalog, order: Order) -> int:
    return int(order_subtotal(catalog, order) * 100)


def projected_annual(revenue_per_day: float, days: int = 365) -> float:
    return revenue_per_day * days


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------


def run(orders_path: str, out_path: str) -> None:
    catalog = Catalog()
    orders = load_orders(orders_path)
    report = summarize(catalog, orders)
    save_report(Path(out_path), [report])
