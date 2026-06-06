import sqlite3
import logging
import os
from datetime import datetime, date

logger = logging.getLogger(__name__)

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "product_memory.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT UNIQUE NOT NULL,
    first_discovered TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    appearance_count INTEGER DEFAULT 1,
    watchlist_confidence REAL DEFAULT 0.0,
    current_momentum REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS discovery_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    discovery_score REAL NOT NULL,
    source TEXT NOT NULL,
    category TEXT,
    discovered_at TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS research_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    product_score REAL NOT NULL,
    confidence_score REAL,
    survival_probability REAL,
    decision TEXT,
    analyzed_at TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE IF NOT EXISTS daily_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    snapshot_date TEXT NOT NULL,
    discovery_score REAL,
    product_score REAL,
    momentum_score REAL,
    UNIQUE(product_id, snapshot_date),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
"""


def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        logger.info(f"Product memory DB initialized at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to initialize DB: {e}")
    finally:
        conn.close()


def _ensure_product(conn, product_name: str) -> int:
    today = date.today().isoformat()
    cursor = conn.execute(
        "SELECT product_id, appearance_count FROM products WHERE product_name = ?",
        (product_name,),
    )
    row = cursor.fetchone()
    if row:
        product_id = row["product_id"]
        conn.execute(
            "UPDATE products SET last_seen = ?, appearance_count = appearance_count + 1 WHERE product_id = ?",
            (today, product_id),
        )
        return product_id
    else:
        cursor = conn.execute(
            "INSERT INTO products (product_name, first_discovered, last_seen, appearance_count) VALUES (?, ?, ?, 1)",
            (product_name, today, today),
        )
        return cursor.lastrowid


def save_discovery_result(product_name: str, discovery_score: float, source: str, category: str = None):
    conn = get_connection()
    try:
        product_id = _ensure_product(conn, product_name)
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO discovery_history (product_id, discovery_score, source, category, discovered_at) VALUES (?, ?, ?, ?, ?)",
            (product_id, discovery_score, source, category, now),
        )
        _update_momentum(conn, product_id, discovery_score)
        _update_watchlist_confidence(conn, product_id)
        conn.commit()
    except Exception as e:
        logger.warning(f"Failed to save discovery result for {product_name}: {e}")
    finally:
        conn.close()


def save_research_result(product_name: str, product_score: float, confidence_score: float = None,
                         survival_probability: float = None, decision: str = None):
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT product_id FROM products WHERE product_name = ?", (product_name,))
        row = cursor.fetchone()
        if not row:
            product_id = _ensure_product(conn, product_name)
        else:
            product_id = row["product_id"]
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO research_history (product_id, product_score, confidence_score, survival_probability, decision, analyzed_at) VALUES (?, ?, ?, ?, ?, ?)",
            (product_id, product_score, confidence_score, survival_probability, decision, now),
        )
        conn.commit()
    except Exception as e:
        logger.warning(f"Failed to save research result for {product_name}: {e}")
    finally:
        conn.close()


def _update_momentum(conn, product_id: int, current_score: float):
    cursor = conn.execute(
        "SELECT discovery_score FROM discovery_history WHERE product_id = ? ORDER BY discovered_at DESC LIMIT 1 OFFSET 1",
        (product_id,),
    )
    row = cursor.fetchone()
    if row:
        previous_score = row["discovery_score"]
        momentum = current_score - previous_score
        conn.execute(
            "UPDATE products SET current_momentum = ? WHERE product_id = ?",
            (round(momentum, 2), product_id),
        )
    else:
        conn.execute(
            "UPDATE products SET current_momentum = 0.0 WHERE product_id = ?",
            (product_id,),
        )


def _update_watchlist_confidence(conn, product_id: int):
    cursor = conn.execute(
        "SELECT first_discovered, last_seen, appearance_count FROM products WHERE product_id = ?",
        (product_id,),
    )
    row = cursor.fetchone()
    if not row:
        return

    first = datetime.fromisoformat(row["first_discovered"]).date()
    last = datetime.fromisoformat(row["last_seen"]).date()
    days_active = (last - first).days + 1

    if days_active >= 30:
        confidence = 20.0
    elif days_active >= 7:
        confidence = 10.0
    else:
        confidence = 0.0

    conn.execute(
        "UPDATE products SET watchlist_confidence = ? WHERE product_id = ?",
        (confidence, product_id),
    )


def get_product_history(product_name: str) -> dict:
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM products WHERE product_name = ?", (product_name,))
        product = cursor.fetchone()
        if not product:
            return None

        cursor = conn.execute(
            "SELECT * FROM discovery_history WHERE product_id = ? ORDER BY discovered_at",
            (product["product_id"],),
        )
        discovery = [dict(r) for r in cursor.fetchall()]

        cursor = conn.execute(
            "SELECT * FROM research_history WHERE product_id = ? ORDER BY analyzed_at",
            (product["product_id"],),
        )
        research = [dict(r) for r in cursor.fetchall()]

        cursor = conn.execute(
            "SELECT * FROM daily_snapshots WHERE product_id = ? ORDER BY snapshot_date",
            (product["product_id"],),
        )
        snapshots = [dict(r) for r in cursor.fetchall()]

        return {
            "product": dict(product),
            "discovery_history": discovery,
            "research_history": research,
            "daily_snapshots": snapshots,
        }
    finally:
        conn.close()


def get_watchlist(min_confidence: float = 0) -> list:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT product_name, appearance_count, watchlist_confidence, current_momentum, last_seen "
            "FROM products WHERE watchlist_confidence >= ? ORDER BY watchlist_confidence DESC, appearance_count DESC",
            (min_confidence,),
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_top_rising(limit: int = 10) -> list:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT p.product_name, p.current_momentum, p.appearance_count, p.watchlist_confidence, "
            "dh.discovery_score, dh.source, dh.discovered_at "
            "FROM products p "
            "JOIN discovery_history dh ON dh.product_id = p.product_id "
            "WHERE dh.discovered_at = (SELECT MAX(discovered_at) FROM discovery_history WHERE product_id = p.product_id) "
            "ORDER BY p.current_momentum DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_top_falling(limit: int = 10) -> list:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT p.product_name, p.current_momentum, p.appearance_count, p.watchlist_confidence, "
            "dh.discovery_score, dh.source, dh.discovered_at "
            "FROM products p "
            "JOIN discovery_history dh ON dh.product_id = p.product_id "
            "WHERE dh.discovered_at = (SELECT MAX(discovered_at) FROM discovery_history WHERE product_id = p.product_id) "
            "ORDER BY p.current_momentum ASC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def get_most_consistent(limit: int = 10) -> list:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT p.product_name, p.appearance_count, p.watchlist_confidence, p.current_momentum, "
            "ROUND(AVG(dh.discovery_score), 2) as avg_score, "
            "ROUND(MAX(dh.discovery_score) - MIN(dh.discovery_score), 2) as score_range "
            "FROM products p "
            "JOIN discovery_history dh ON dh.product_id = p.product_id "
            "GROUP BY p.product_id "
            "HAVING COUNT(dh.id) > 1 "
            "ORDER BY score_range ASC, p.appearance_count DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()


def save_daily_snapshot():
    conn = get_connection()
    try:
        today = date.today().isoformat()
        cursor = conn.execute("SELECT product_id, current_momentum FROM products")
        products = cursor.fetchall()

        for p in products:
            pid = p["product_id"]
            cursor = conn.execute(
                "SELECT discovery_score FROM discovery_history WHERE product_id = ? ORDER BY discovered_at DESC LIMIT 1",
                (pid,),
            )
            disc_row = cursor.fetchone()
            disc_score = disc_row["discovery_score"] if disc_row else None

            cursor = conn.execute(
                "SELECT product_score FROM research_history WHERE product_id = ? ORDER BY analyzed_at DESC LIMIT 1",
                (pid,),
            )
            res_row = cursor.fetchone()
            res_score = res_row["product_score"] if res_row else None

            conn.execute(
                "INSERT OR REPLACE INTO daily_snapshots (product_id, snapshot_date, discovery_score, product_score, momentum_score) "
                "VALUES (?, ?, ?, ?, ?)",
                (pid, today, disc_score, res_score, p["current_momentum"]),
            )

        conn.commit()
        logger.info(f"Daily snapshot saved for {len(products)} products")
    except Exception as e:
        logger.warning(f"Failed to save daily snapshot: {e}")
    finally:
        conn.close()


def print_watchlist():
    items = get_watchlist()
    if not items:
        print("  (empty)")
        return
    print(f"  {'Product':<35} {'Appearances':<12} {'Confidence':<12} {'Momentum':<10} {'Last Seen':<14}")
    print(f"  " + "-" * 83)
    for r in items:
        print(f"  {r['product_name'][:33]:<35} {r['appearance_count']:<12} {r['watchlist_confidence']:<12.0f} {r['current_momentum']:<+10.1f} {r['last_seen'][:12]:<14}")


def print_rising(limit=10):
    items = get_top_rising(limit)
    if not items:
        print("  (no data)")
        return
    print(f"  {'Product':<35} {'Momentum':<10} {'Score':<8} {'Source':<14}")
    print(f"  " + "-" * 67)
    for r in items:
        print(f"  {r['product_name'][:33]:<35} {r['current_momentum']:<+10.1f} {r['discovery_score']:<8.0f} {r['source'][:14]:<14}")


def print_falling(limit=10):
    items = get_top_falling(limit)
    if not items:
        print("  (no data)")
        return
    print(f"  {'Product':<35} {'Momentum':<10} {'Score':<8} {'Source':<14}")
    print(f"  " + "-" * 67)
    for r in items:
        print(f"  {r['product_name'][:33]:<35} {r['current_momentum']:<+10.1f} {r['discovery_score']:<8.0f} {r['source'][:14]:<14}")


def print_consistent(limit=10):
    items = get_most_consistent(limit)
    if not items:
        print("  (no data)")
        return
    print(f"  {'Product':<35} {'Avg Score':<10} {'Range':<8} {'Appearances':<12} {'Confidence':<10}")
    print(f"  " + "-" * 75)
    for r in items:
        print(f"  {r['product_name'][:33]:<35} {r['avg_score']:<10.1f} {r['score_range']:<8.1f} {r['appearance_count']:<12} {r['watchlist_confidence']:<10.0f}")


def print_product_detail(product_name: str):
    data = get_product_history(product_name)
    if not data:
        print(f"  Product '{product_name}' not found in memory")
        return

    p = data["product"]
    print(f"  Product: {p['product_name']}")
    print(f"  First seen: {p['first_discovered']}")
    print(f"  Last seen: {p['last_seen']}")
    print(f"  Appearances: {p['appearance_count']}")
    print(f"  Watchlist confidence: {p['watchlist_confidence']:.0f}")
    print(f"  Current momentum: {p['current_momentum']:+.1f}")
    print()

    disc = data["discovery_history"]
    if disc:
        print(f"  Discovery History ({len(disc)} entries):")
        print(f"  {'#':<4} {'Score':<8} {'Source':<16} {'Category':<12} {'Date':<20}")
        print(f"  " + "-" * 60)
        for i, r in enumerate(disc, 1):
            print(f"  {i:<4} {r['discovery_score']:<8.0f} {r['source'][:14]:<16} {str(r.get('category',''))[:10]:<12} {r['discovered_at'][:19]:<20}")
        print()

    res = data["research_history"]
    if res:
        print(f"  Research History ({len(res)} entries):")
        print(f"  {'#':<4} {'Score':<8} {'Confidence':<12} {'Decision':<14} {'Date':<20}")
        print(f"  " + "-" * 58)
        for i, r in enumerate(res, 1):
            print(f"  {i:<4} {r['product_score']:<8.0f} {r.get('confidence_score',0):<12.0f} {str(r.get('decision',''))[:12]:<14} {r['analyzed_at'][:19]:<20}")


def memory_main():
    init_db()
    print()
    print("=" * 60)
    print("  PRODUCT MEMORY SYSTEM")
    print("=" * 60)
    print()
    print("  Watchlist:")
    print_watchlist()
    print()
    print("  Top Rising Products:")
    print_rising()
    print()
    print("  Top Falling Products:")
    print_falling()
    print()
    print("  Most Consistent Products:")
    print_consistent()


if __name__ == "__main__":
    memory_main()
