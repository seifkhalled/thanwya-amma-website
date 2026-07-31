# Thanaweya Amma 2026 Results

A FastAPI web app for searching Egyptian high school (Thanaweya Amma) exam results, with an interactive statistics dashboard.

## Features

- **Search** by student name (full or partial) or seating number
- **Dashboard** (`/dashboard`) with Plotly Express charts:
  - Score distribution histogram with KDE curve
  - Result breakdown donut (pass / second round / fail / absent)
  - Box plot of scores by result case
  - Cumulative score curve with percentile markers
  - Top 20 highest-scoring students
  - Score bands (students per 10-degree bucket)
  - KPI cards (total students, pass rates, average, median, failed count)

## Quick Start

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860

Open http://127.0.0.1:7860 in your browser.
```

- Search page: http://127.0.0.1:7860/
- Dashboard: http://127.0.0.1:7860/dashboard

## Deploy on Hugging Face Spaces

1. Create a new Space on [huggingface.co/spaces](https://huggingface.co/spaces)
2. Choose "Docker" or "Blank" SDK
3. Push this repo
4. The app will auto-start on port 7860

Or use the CLI:

```bash
huggingface-cli login
huggingface-cli repo create your-space-name --type space --sdk docker
git remote add space https://huggingface.co/spaces/your-username/your-space-name
git push space main
```

## Usage

- **Search by name**: enter a student's name (full or partial)
- **Search by ID**: enter the student's seating number
- **Dashboard**: open the stats dashboard from the button in the header, or visit `/dashboard`
