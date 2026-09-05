# Brawl Stars Character Quiz (Django)

Guess the Brawl Stars brawler from the image — four English-name multiple choice options.

> **Note:** GitHub Pages cannot host Django. Run locally (or on any WSGI/ASGI server).
> The old static site lives in [`legacy_static/`](./legacy_static/).

## Character DB (source of truth)

Quiz roster comes from the `Character` model — **not** from a live BrawlAPI call at request time.

A character appears in the quiz only when **both** are true:

- `is_active=True`
- `image_kind=full_body`

Images are stored as **URLs only** (no media uploads yet). The quiz payload exposes a single `image_url` (no multi-URL fallback chain).

| Field | Role |
|--------|------|
| `name_en` | Unique key (English) |
| `display_name` | Shown in choices / reveal |
| `image_url` | Quiz image (curated; sync never overwrites existing) |
| `image_kind` | `full_body` / `portrait` / `unknown` |
| `is_active` | Must be true for quiz |
| `source` | `brawlapi` / `manual` / `extra` |
| `api_image_url` | Optional API portrait; not used in quiz |

### Sync rules (`sync_characters`)

- **New** rows: provisional noff.gg full-body slug URL, `image_kind=unknown`, `is_active=False`
- **Existing** rows: update `display_name`, `color`, `api_id` only — **never** overwrite `image_url` / `image_kind` / `is_active`
- Exclusions (`EXCLUDED_ENGLISH_NAMES`): not created; existing rows deactivated
- Extras (`EXTRA_BRAWLERS`): upserted with `source=extra`

**Important:** A fresh sync leaves almost everyone inactive until you verify and/or activate in Admin.

### Verify helper (`verify_character_images`)

Probes `image_url` (HEAD, then GET if needed) for inactive/unknown rows:

- HTTP 200 → set `image_kind=full_body`
- If the URL is a noff full-body path → also set `is_active=True` (so first run is usable)
- Other 200s → `full_body` only; leave `is_active=False` for human review

## Requirements

- Python 3.10+ (3.12 / 3.13 recommended)
- Internet access for `sync_characters` / `verify_character_images`

## Setup (local)

```bash
cd /path/to/brawl-quiz
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# DB schema
python manage.py migrate

# Populate Character from BrawlAPI + extras (most stay inactive)
python manage.py sync_characters

# Optional: probe provisional URLs; activate noff full-body hits
python manage.py verify_character_images

# Create a superuser, then open /admin/ to curate image_url / image_kind / is_active
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ for the quiz and http://127.0.0.1:8000/admin/ for Character admin.

If fewer than 4 active full-body characters exist, APIs return HTTP 503 with an English message telling you to sync + verify/activate.

### Useful flags

```bash
python manage.py sync_characters --dry-run
python manage.py verify_character_images --dry-run --limit 20
```

## Architecture

- `config/` — Django project settings
- `quiz/` — quiz app
  - `models.py` — `Character`
  - `admin.py` — edit image / active flags
  - `management/commands/sync_characters.py` — BrawlAPI → DB
  - `management/commands/verify_character_images.py` — URL probe helper
  - `characters_config.py` — exclusions / extras / slug overrides
  - `services.py` — DB roster + question logic
  - JSON APIs: `/api/start/`, `/api/answer/`, `/api/next/`, `/api/status/`

## Legacy static site

`legacy_static/` keeps the previous static files for a GitHub Pages–style deploy.
