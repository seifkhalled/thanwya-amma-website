import re
from pathlib import Path

import app as appmod

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
TPL_DASH = ROOT / "templates" / "dashboard.html"
TPL_SEARCH = ROOT / "templates" / "index.html"


def build_dashboard():
    html = TPL_DASH.read_text(encoding="utf-8")
    for key, value in appmod.charts_html().items():
        html = html.replace(f"<!--{key.upper()}-->", value)
    html = html.replace("<!--STATS-->", "")
    html = html.replace('href="/dashboard"', 'href="index.html"')
    html = html.replace('href="/"', 'href="search.html"')
    html = html.replace(
        '© 2026 — جميع الحقوق محفوظة',
        '© 2026 — جميع الحقوق محفوظة · لوحة إحصائيات ثابتة',
    )
    return html


def build_search():
    html = TPL_SEARCH.read_text(encoding="utf-8")
    html = html.replace("<!--STATS-->", "")
    html = html.replace('href="/dashboard"', 'href="index.html"')
    html = html.replace('href="/"', 'href="search.html"')
    html = re.sub(r'\sonclick="[^"]*"', "", html)
    html = re.sub(
        r"<script>.*</script>",
        '<script src="meta.js"></script>\n<script src="search.js"></script>',
        html,
        flags=re.S,
    )
    return html


def main():
    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(build_dashboard(), encoding="utf-8")
    (OUT / "search.html").write_text(build_search(), encoding="utf-8")
    print("Static site generated in", OUT)


if __name__ == "__main__":
    main()
