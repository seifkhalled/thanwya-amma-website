import sqlite3
import datetime
from pathlib import Path

DB = Path(__file__).parent / "stats.db"


def init_db():
    with sqlite3.connect(str(DB)) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS page_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT, dt TEXT
            );
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT,
                results_count INTEGER, dt TEXT
            );
        """)


def visit():
    with sqlite3.connect(str(DB)) as conn:
        conn.execute("INSERT INTO page_views (dt) VALUES (?)",
                     (datetime.datetime.utcnow().isoformat(),))
        conn.commit()


def record_search(query, n):
    with sqlite3.connect(str(DB)) as conn:
        conn.execute("INSERT INTO searches (query, results_count, dt) VALUES (?, ?, ?)",
                     (query, n, datetime.datetime.utcnow().isoformat()))
        conn.commit()


def stats_html():
    with sqlite3.connect(str(DB)) as conn:
        total = conn.execute("SELECT COUNT(*) FROM page_views").fetchone()[0]
        sc = conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0]
    return f"""<div class="stats-bar"><span>المشاهدات: <strong>{total:,}</strong></span><span>عمليات البحث: <strong>{sc:,}</strong></span></div>"""
