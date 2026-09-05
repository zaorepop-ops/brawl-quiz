# Brawl Stars Character Quiz (Django)

Guess the Brawl Stars brawler from the image — four English-name multiple choice options.
The server manages roster fetch, question selection, and scoring.

> **Note:** GitHub Pages cannot host Django.
> Run locally (or on any WSGI/ASGI server) for now.
> The old static site lives in [`legacy_static/`](./legacy_static/).

## Requirements

- Python 3.10+ (3.12 / 3.13 recommended)
- Internet access (loads [BrawlAPI](https://api.brawlapi.com/v1/brawlers) on startup / cache refresh)

## Setup (local)

```bash
cd /path/to/brawl-quiz
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

## Architecture

- `config/` — Django project settings
- `quiz/` — quiz app
  - `characters_config.py` — exclusions / extras / image slug overrides (display names are English)
  - `services.py` — BrawlAPI fetch, in-memory cache, question logic
  - Session stores the answer, score, and question deck
  - JSON APIs: `/api/start/`, `/api/answer/`, `/api/next/`, `/api/status/`
  - Front end: `quiz/static/quiz/quiz.js` calls the APIs; UI copy is English

## Legacy static site

`legacy_static/` keeps the previous `index.html` / `script.js` / `characters.js` / `styles.css`.
Use that if you need a GitHub Pages–style static deploy.
