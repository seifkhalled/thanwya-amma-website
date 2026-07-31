# Thanaweya Amma 2026 Results

Search Egyptian high school (Thanaweya Amma) 2026 exam results by name or seating number, with an interactive statistics dashboard.

The deployed website is **fully static** (free hosting on GitHub Pages, no backend):

- **Dashboard** (`docs/index.html`): all 6 Plotly charts and KPI cards are pre-rendered and embedded in the page — no server needed.
- **Search** (`docs/search.html`): the search page downloads a compressed dataset (`docs/data.gz`, ~12 MB) into the browser and searches locally. First load is slower (downloads the dataset once); repeat visits are fast thanks to browser caching.

## Repo layout

| Path | Purpose |
| --- | --- |
| `docs/` | Generated static website (GitHub Pages serves this folder) |
| `build_static.py` | Renders `docs/index.html` + `docs/search.html` from the templates |
| `build_data_files.py` | Builds `docs/data.gz` (compact binary dataset) + `docs/meta.js` |
| `verify_data.py` | Checks the binary format / search algorithm against the source parquet |
| `templates/` | Source templates for the live pages |
| `app.py`, `data.py`, `db.py` | Local FastAPI dev preview (`/` search, `/dashboard`) |
| `نتيجة ثانوية عامة نظام حديث.parquet` | Source dataset (919,396 rows) |

## Rebuild the static site

```bash
pip install -r requirements.txt
python -X utf8 build_data_files.py   # rebuild docs/data.gz from the parquet
python -X utf8 build_static.py       # regenerate docs/index.html + docs/search.html
```

## Local development

```bash
uvicorn app:app --host 0.0.0.0 --port 7860
```

- Search page: http://127.0.0.1:7860/
- Dashboard: http://127.0.0.1:7860/dashboard

## Deploy (GitHub Pages)

1. Push `master` to GitHub.
2. Repo → Settings → Pages → Source: **Deploy from a branch** → branch `master`, folder `/docs`.
3. The site is served at `https://<user>.github.io/<repo>/`.
