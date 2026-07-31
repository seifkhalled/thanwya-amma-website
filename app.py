import pandas as pd
import sqlite3
import datetime
import json
from functools import lru_cache
from pathlib import Path
import numpy as np
from scipy.stats import gaussian_kde
import plotly.graph_objects as go
import plotly.express as px
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

PARQUET = Path(__file__).parent / "نتيجة ثانوية عامة نظام حديث.parquet"
df = pd.read_parquet(PARQUET).fillna("")

DB = Path(__file__).parent / "stats.db"

CASE_COLORS = {
    "ناجح دور أول": "#22c55e",
    "دور ثان": "#f59e0b",
    "راسب دور أول": "#ef4444",
    "غياب كلى دور أول": "#94a3b8",
}

TPL = go.layout.Template(
    layout=dict(
        font=dict(family="Cairo, sans-serif", color="#1e293b"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin=dict(l=10, r=10, t=20, b=10),
        hoverlabel=dict(font_family="Cairo", font_size=13, bgcolor="#1e293b"),
        xaxis=dict(gridcolor="#eef2ff", zeroline=False, linecolor="#e2e8f0", tickfont=dict(size=12)),
        yaxis=dict(gridcolor="#eef2ff", zeroline=False, linecolor="#e2e8f0", tickfont=dict(size=12)),
        colorway=["#6366f1", "#8b5cf6", "#22c55e", "#f59e0b", "#ef4444", "#0ea5e9"],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=12)),
    )
)


def style_fig(fig, height=420):
    fig.update_layout(template=TPL, height=height, showlegend=False)
    fig.update_xaxes(title_font=dict(size=13, color="#64748b"))
    fig.update_yaxes(title_font=dict(size=13, color="#64748b"))
    return fig


def fig_html(fig, height=420):
    style_fig(fig, height)
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True},
    )


@lru_cache(maxsize=1)
def dashboard_data():
    scores = df["total_degree"].to_numpy()
    n = len(scores)

    case_counts = df["student_case_desc"].value_counts()
    pass1 = int(case_counts.get("ناجح دور أول", 0))
    second = int(case_counts.get("دور ثان", 0))
    failed = int(case_counts.get("راسب دور أول", 0))
    absent = int(case_counts.get("غياب كلى دور أول", 0))

    return dict(
        scores=scores,
        n=n,
        pass1=pass1,
        second=second,
        failed=failed,
        absent=absent,
        pass1_rate=pass1 / n * 100,
        pass_all_rate=(pass1 + second) / n * 100,
        avg=float(np.mean(scores)),
        median=float(np.median(scores)),
        max_score=float(scores.max()),
    )


def kpi_cards_html():
    d = dashboard_data()
    cards = [
        ("إجمالي الطلاب", f"{d['n']:,}", "#6366f1", "👥"),
        ("نسبة النجاح دور أول", f"{d['pass1_rate']:.2f}%", "#22c55e", "✅"),
        ("نسبة النجاح الكلية", f"{d['pass_all_rate']:.2f}%", "#0ea5e9", "🎯"),
        ("المتوسط العام", f"{d['avg']:.2f}", "#8b5cf6", "📊"),
        ("الوسيط", f"{d['median']:.2f}", "#f59e0b", "📈"),
        ("عدد الراسبين", f"{d['failed']:,}", "#ef4444", "❌"),
    ]
    items = "".join(
        f"""<div class="kpi-card" style="--accent:{color}">
          <div class="kpi-icon">{icon}</div>
          <div class="kpi-value">{value}</div>
          <div class="kpi-label">{label}</div>
        </div>"""
        for label, value, color, icon in cards
    )
    return f'<div class="kpi-grid">{items}</div>'


def chart_hist_html():
    d = dashboard_data()
    scores = d["scores"]
    counts, edges = np.histogram(scores, bins=80, range=(0, 320))
    centers = (edges[:-1] + edges[1:]) / 2
    width = edges[1] - edges[0]

    rng = np.random.default_rng(42)
    sample = scores[np.sort(rng.choice(len(scores), size=60000, replace=False))]
    kde = gaussian_kde(sample)
    grid = np.linspace(0, 320, 400)

    fig = px.bar(
        x=centers, y=counts,
        labels={"x": "الدرجة", "y": "عدد الطلاب"},
    )
    fig.add_trace(go.Scatter(
        x=grid, y=kde(grid) * len(scores) * width,
        mode="lines", name="منحنى التوزيع",
        line=dict(color="#f59e0b", width=3),
    ))
    fig.update_traces(marker_color="#6366f1", marker_opacity=0.8)
    fig.add_vline(x=d["median"], line_dash="dash", line_color="#ef4444",
                  annotation_text=f"الوسيط {d['median']:.1f}", annotation_font_color="#ef4444",
                  annotation_position="top left")
    return fig_html(fig)


def chart_pie_html():
    d = dashboard_data()
    labels = ["ناجح دور أول", "دور ثان", "راسب دور أول", "غياب كلى دور أول"]
    values = [d["pass1"], d["second"], d["failed"], d["absent"]]
    fig = px.pie(
        values=values, names=labels, hole=0.55,
        color=labels, color_discrete_map=CASE_COLORS,
    )
    fig.update_traces(
        textinfo="percent+label",
        textfont=dict(size=13),
        hovertemplate="%{label}<br>%{value:,} طالب (%{percent})<extra></extra>",
    )
    fig.update_layout(showlegend=False, height=420, template=TPL)
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True},
    )


def chart_box_html():
    sample = df.sample(n=12000, random_state=42)
    fig = px.box(
        sample, x="student_case_desc", y="total_degree", points=False,
        color="student_case_desc", color_discrete_map=CASE_COLORS,
        labels={"student_case_desc": "", "total_degree": "الدرجة"},
    )
    fig.update_layout(showlegend=False, template=TPL, height=420)
    fig.update_yaxes(title_font=dict(size=13, color="#64748b"))
    fig.update_xaxes(title_font=dict(size=13, color="#64748b"))
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True},
    )


def chart_cumulative_html():
    d = dashboard_data()
    grid = np.arange(0, 321)
    pct = np.searchsorted(np.sort(d["scores"]), grid, side="right") / d["n"] * 100
    fig = px.line(
        x=grid, y=pct,
        labels={"x": "الدرجة", "y": "النسبة التراكمية (%)"},
    )
    fig.update_traces(line=dict(color="#8b5cf6", width=3), fill="tozeroy", fillcolor="rgba(139,92,246,.1)")
    for y, label in ((10, "أعلى 10%"), (50, "الوسيط 50%"), (90, "أدنى 90%")):
        fig.add_hline(y=y, line_dash="dot", line_color="#94a3b8",
                      annotation_text=label, annotation_position="top left",
                      annotation_font_size=12)
    return fig_html(fig)


def chart_top_html():
    top = df.nlargest(20, "total_degree").iloc[::-1]
    fig = px.bar(
        top, x="total_degree", y="arabic_name", orientation="h",
        color="total_degree",
        color_continuous_scale=["#dbeafe", "#6366f1", "#4f46e5"],
        labels={"total_degree": "الدرجة", "arabic_name": ""},
        hover_data={"seating_no": True, "arabic_name": False},
    )
    fig.update_layout(
        showlegend=False, template=TPL, height=520,
        coloraxis_showscale=False,
    )
    fig.update_xaxes(title_font=dict(size=13, color="#64748b"))
    fig.update_yaxes(title_font=dict(size=13, color="#64748b"))
    return fig.to_html(
        full_html=False,
        include_plotlyjs=False,
        config={"displayModeBar": False, "responsive": True},
    )


def chart_bands_html():
    d = dashboard_data()
    bins = list(range(0, 321, 10))
    labels = [f"{i}-{i + 10}" for i in range(0, 310, 10)] + ["310-320"]
    counts, _ = np.histogram(d["scores"], bins=bins)
    fig = px.bar(
        x=labels, y=counts,
        labels={"x": "شريحة الدرجات", "y": "عدد الطلاب"},
    )
    fig.update_traces(marker_color="#6366f1", marker_opacity=0.85)
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=11))
    return fig_html(fig)


@lru_cache(maxsize=1)
def charts_html():
    return {
        "kpi": kpi_cards_html(),
        "hist": chart_hist_html(),
        "pie": chart_pie_html(),
        "box": chart_box_html(),
        "cum": chart_cumulative_html(),
        "top": chart_top_html(),
        "bands": chart_bands_html(),
    }

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

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def index():
    visit()
    html = Path(__file__).parent.joinpath("templates", "index.html").read_text(encoding="utf-8")
    html = html.replace("<!--STATS-->", stats_html())
    return HTMLResponse(html)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    visit()
    html = Path(__file__).parent.joinpath("templates", "dashboard.html").read_text(encoding="utf-8")
    html = html.replace("<!--STATS-->", stats_html())
    for key, value in charts_html().items():
        html = html.replace(f"<!--{key.upper()}-->", value)
    return HTMLResponse(html)

@app.get("/search")
async def search(q: str = Query(...), by: str = Query("name")):
    visit()
    q = q.strip()
    if not q:
        return []

    if by == "id":
        try:
            sid = int(q)
        except ValueError:
            return []
        result = df[df["seating_no"] == sid]
    else:
        parts = q.split()
        mask = pd.Series(True, index=df.index)
        for p in parts:
            mask &= df["arabic_name"].str.replace(" ", "", regex=False).str.contains(
                p.replace(" ", ""), case=False, na=False
            )
        result = df[mask]

    data = json.loads(result.head(50).to_json(orient="records"))
    record_search(q, len(data))
    return data
