import gradio as gr
import pandas as pd
import sqlite3
import datetime
from pathlib import Path

PARQUET = Path(__file__).parent / "نتيجة ثانوية عامة نظام حديث.parquet"
df = pd.read_parquet(PARQUET).fillna("")

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

init_db()

def visit():
    with sqlite3.connect(str(DB)) as conn:
        conn.execute("INSERT INTO page_views (dt) VALUES (?)", (datetime.datetime.utcnow().isoformat(),))
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

def status_class(s):
    s = (s or "").lower()
    if "ناجح" in s: return "status-pass"
    if "دور ثان" in s: return "status-second"
    return "status-fail"

def search_fn(q, by):
    visit()
    q = q.strip()
    if not q:
        return stats_html(), ""

    if by == "id":
        try:
            sid = int(q)
        except ValueError:
            return stats_html(), '<div class="error-msg">رقم جلوس غير صالح</div>'
        result = df[df["seating_no"] == sid]
    else:
        parts = q.split()
        mask = pd.Series(True, index=df.index)
        for p in parts:
            mask &= df["arabic_name"].str.replace(" ", "", regex=False).str.contains(p.replace(" ", ""), case=False, na=False)
        result = df[mask]

    if result.empty:
        record_search(q, 0)
        return stats_html(), '<div class="no-results">لا توجد نتائج للبحث</div>'

    data = result.head(50)
    record_search(q, len(data))
    count = f'<div class="results-count">تم العثور على {len(data)} نتيجة</div>'
    cards = data.apply(lambda s: f"""
        <div class="result-card">
            <div class="result-info">
                <div class="result-name">{s["arabic_name"]}</div>
                <div class="result-id">رقم الجلوس: <span>{s["seating_no"]}</span></div>
            </div>
            <div class="result-meta">
                <div class="degree"><div class="degree-value">{s["total_degree"]}</div><span class="degree-label">الدرجة</span></div>
                <div class="status-badge {status_class(s["student_case_desc"])}">{s["student_case_desc"]}</div>
            </div>
        </div>""", axis=1).str.cat(sep="")
    return stats_html(), count + cards

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');
:root { --primary: #6366f1; --primary-dark: #4f46e5; --bg: #f0f2f5; --card-bg: #fff; --text: #1e293b; --text-secondary: #64748b; --border: #e2e8f0; --radius: 16px; --radius-sm: 10px; --shadow: 0 1px 3px rgba(0,0,0,.06); --shadow-lg: 0 10px 40px rgba(99,102,241,.15); }
* { font-family: 'Cairo', sans-serif !important; }
.gradio-container { max-width: 720px !important; margin: 0 auto !important; padding: 0 !important; background: var(--bg) !important; }
.gradio-container .main { padding: 0 !important; }
.hero { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%); padding: 40px 20px 60px; text-align: center; position: relative; overflow: hidden; }
.hero::before { content: ''; position: absolute; inset: 0; background: radial-gradient(circle at 20% 50%, rgba(255,255,255,.15) 0%, transparent 50%), radial-gradient(circle at 80% 50%, rgba(255,255,255,.1) 0%, transparent 50%); }
.hero h1 { font-size: 32px; font-weight: 800; color: #fff; position: relative; text-shadow: 0 2px 4px rgba(0,0,0,.1); }
.hero p { color: rgba(255,255,255,.85); font-size: 16px; margin-top: 8px; position: relative; }
.stats-bar { display: flex; justify-content: center; gap: 32px; margin: -36px auto 20px; font-size: 14px; color: var(--text-secondary); background: var(--card-bg); border-radius: var(--radius); padding: 14px 24px; box-shadow: var(--shadow); border: 1px solid var(--border); flex-wrap: wrap; max-width: 720px; }
.stats-bar strong { color: var(--text); font-weight: 700; }
.search-box { background: var(--card-bg); border-radius: var(--radius); padding: 20px 24px 24px; box-shadow: var(--shadow-lg); margin-bottom: 20px; }
.gr-box { border: none !important; background: transparent !important; box-shadow: none !important; }
.gr-form { border: none !important; background: transparent !important; }
/* radio as tabs */
#search-mode { display: flex !important; flex-direction: row !important; gap: 4px !important; background: #f1f5f9 !important; border-radius: 10px !important; padding: 4px !important; margin-bottom: 16px !important; }
#search-mode label { flex: 1; text-align: center; margin: 0 !important; padding: 0 !important; }
#search-mode label input { display: none; }
#search-mode label span { display: block; padding: 10px; font-size: 14px; font-weight: 600; border-radius: 8px; cursor: pointer; color: var(--text-secondary); transition: all .2s; }
#search-mode label input:checked + span { background: var(--card-bg); color: var(--primary); box-shadow: 0 1px 3px rgba(0,0,0,.08); }
/* input row */
.input-row { display: flex; gap: 8px; }
#search-input { border: 2px solid var(--border) !important; border-radius: var(--radius-sm) !important; padding: 14px 18px !important; font-size: 16px !important; background: #fafafa !important; box-shadow: none !important; }
#search-input:focus { border-color: var(--primary) !important; box-shadow: 0 0 0 4px rgba(99,102,241,.12) !important; background: #fff !important; }
#search-btn { background: linear-gradient(135deg, var(--primary), var(--primary-dark)) !important; color: #fff !important; border: none !important; border-radius: var(--radius-sm) !important; padding: 14px 32px !important; font-size: 16px !important; font-weight: 700 !important; cursor: pointer !important; min-width: 100px; text-align: center; }
#search-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(99,102,241,.4) !important; }
/* results */
.result-card { background: var(--card-bg); border-radius: var(--radius); padding: 20px 24px; box-shadow: var(--shadow); margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; border: 1px solid var(--border); }
.result-name { font-size: 18px; font-weight: 700; }
.result-id { font-size: 13px; color: var(--text-secondary); }
.result-id span { color: var(--text); font-weight: 600; }
.result-meta { display: flex; align-items: center; gap: 16px; }
.degree { text-align: center; }
.degree-value { font-size: 28px; font-weight: 800; color: var(--primary); line-height: 1; }
.degree-label { font-size: 11px; color: var(--text-secondary); display: block; }
.status-badge { padding: 6px 16px; border-radius: 20px; font-size: 13px; font-weight: 700; white-space: nowrap; }
.status-pass { background: linear-gradient(135deg, #dcfce7, #bbf7d0); color: #166534; }
.status-fail { background: linear-gradient(135deg, #fef2f2, #fecaca); color: #991b1b; }
.status-second { background: linear-gradient(135deg, #fef9c3, #fde68a); color: #854d0e; }
.no-results { text-align: center; padding: 48px 20px; color: var(--text-secondary); font-size: 16px; }
.error-msg { text-align: center; padding: 24px 20px; color: #dc2626; font-size: 15px; background: #fef2f2; border-radius: var(--radius); margin: 8px 0; }
.results-count { font-size: 14px; color: var(--text-secondary); text-align: center; margin-bottom: 12px; }
.linkedin-bar { text-align: center; margin: 20px 0; }
.linkedin-bar a { display: inline-flex; align-items: center; gap: 8px; background: #0a66c2; color: #fff; padding: 10px 24px; border-radius: 50px; text-decoration: none; font-size: 15px; font-weight: 700; transition: all .2s; }
.linkedin-bar a:hover { background: #004182; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(10,102,194,.35); }
.footer { text-align: center; padding: 32px 20px; color: var(--text-secondary); font-size: 13px; }
@media (max-width: 600px) {
  .hero h1 { font-size: 24px; }
  .hero { padding: 28px 16px 48px; }
  .stats-bar { margin-top: -28px; gap: 16px; font-size: 13px; }
  .result-card { flex-direction: column; align-items: flex-start; }
  .result-meta { width: 100%; justify-content: space-between; }
  .degree-value { font-size: 24px; }
}
"""

HERO = """<div class="hero"><h1>نتيجة الثانوية العامة 2026</h1><p>البحث عن النتيجة بواسطة الاسم أو رقم الجلوس</p></div>"""
LINKEDIN = """<div class="linkedin-bar"><a href="https://www.linkedin.com/in/seif-khaled-83bb99252/" target="_blank" rel="noopener"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg> Seif Khaled</a></div>"""
FOOTER = """<div class="footer">© 2026 — جميع الحقوق محفوظة</div>"""

with gr.Blocks(css=CSS, title="نتيجة الثانوية العامة 2026", theme=gr.themes.Base()) as demo:
    gr.HTML(HERO)
    stats_out = gr.HTML(stats_html())

    with gr.Group(elem_classes="search-box"):
        by = gr.Radio(choices=["بحث بالاسم", "بحث برقم الجلوس"], value="بحث بالاسم", label="", elem_id="search-mode", container=False)
        with gr.Row():
            q = gr.Textbox(label="", placeholder="ادخل اسم الطالب...", elem_id="search-input", container=False)
            btn = gr.Button("بحث", elem_id="search-btn")

    results_out = gr.HTML("")
    gr.HTML(LINKEDIN)
    gr.HTML(FOOTER)

    def wrapper(q_val, by_val):
        by_key = "name" if by_val == "بحث بالاسم" else "id"
        return search_fn(q_val, by_key)

    btn.click(wrapper, inputs=[q, by], outputs=[stats_out, results_out])
    q.submit(wrapper, inputs=[q, by], outputs=[stats_out, results_out])
