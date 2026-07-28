import sqlite3
import datetime
from pathlib import Path
from contextlib import contextmanager

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
import pandas as pd

PARQUET = Path(__file__).parent / "نتيجة ثانوية عامة نظام حديث.parquet"
df = pd.read_parquet(PARQUET).fillna("")

app = FastAPI(title="نتيجة الثانوية العامة 2026")
DB = Path(__file__).parent / "stats.db"


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS page_views (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT,
                user_agent TEXT,
                page TEXT,
                dt TEXT
            );
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT,
                query TEXT,
                results_count INTEGER,
                dt TEXT
            );
        """)


@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB))
    try:
        yield conn
    finally:
        conn.close()


def record_page_view(ip: str, user_agent: str, page: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO page_views (ip, user_agent, page, dt) VALUES (?, ?, ?, ?)",
            (ip, user_agent, page, datetime.datetime.utcnow().isoformat()),
        )
        conn.commit()


def record_search(ip: str, query: str, results_count: int):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO searches (ip, query, results_count, dt) VALUES (?, ?, ?, ?)",
            (ip, query, results_count, datetime.datetime.utcnow().isoformat()),
        )
        conn.commit()


init_db()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")
    record_page_view(ip, ua, "/")
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM page_views").fetchone()[0]
        unique = conn.execute("SELECT COUNT(DISTINCT ip) FROM page_views").fetchone()[0]
        search_count = conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0]
    html = (Path(__file__).parent / "templates" / "index.html").read_text(encoding="utf-8")
    html = html.replace("<!--STATS-->", f"""
    <div class="stats">
      <span>المشاهدات: <strong>{total:,}</strong></span>
      <span>الزوار: <strong>{unique:,}</strong></span>
      <span>عمليات البحث: <strong>{search_count:,}</strong></span>
    </div>
    """)
    return html


@app.get("/search")
async def search(
    request: Request,
    q: str = Query(..., description="search query"),
    by: str = Query("name", description="search by name or id"),
):
    ip = request.client.host if request.client else "unknown"
    q = q.strip()
    if not q:
        record_search(ip, q, 0)
        return []

    if by == "id":
        try:
            sid = int(q)
        except ValueError:
            return {"error": "رقم جلوس غير صالح"}
        result = df[df["seating_no"] == sid]
    else:
        parts = q.split()
        mask = pd.Series(True, index=df.index)
        for p in parts:
            pn = p.replace(" ", "")
            mask &= (
                df["arabic_name"]
                .str.replace(" ", "", regex=False)
                .str.contains(pn, case=False, na=False)
            )
        result = df[mask]

    results = [] if result.empty else result.head(50).to_dict(orient="records")
    record_search(ip, q, len(results))
    return results


@app.get("/stats")
async def stats():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM page_views").fetchone()[0]
        unique = conn.execute("SELECT COUNT(DISTINCT ip) FROM page_views").fetchone()[0]
        search_count = conn.execute("SELECT COUNT(*) FROM searches").fetchone()[0]
        today = datetime.date.today().isoformat()
        today_views = conn.execute(
            "SELECT COUNT(*) FROM page_views WHERE dt >= ?", (today,)
        ).fetchone()[0]
    return {
        "total_views": total,
        "unique_visitors": unique,
        "total_searches": search_count,
        "today_views": today_views,
    }
