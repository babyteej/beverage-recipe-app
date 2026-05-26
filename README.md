# Beverage Recipe & Knowledge Base

A personal recipe and ingredient knowledge base for health-and-wellness beverages — cold-press juices, smoothies, teas, tonics, infusions, cold brews, fermented drinks, and decoctions.

**Repository:** [github.com/babyteej/beverage-recipe-app](https://github.com/babyteej/beverage-recipe-app)

The database is the product. AI-seeded entries live in an **unverified pool** until manually upgraded; the UI keeps verified and unverified data strictly separate.

---

## Current status

| Area | Status |
|------|--------|
| Supabase schema + API | Live |
| React frontend | Live (8 pages) |
| AI ingredient seeding | Working (`pending_review/` → Supabase) |
| Verification workflow | Working (queue + structured edit form) |
| Combination engine | Working (anchor + goal modes) |
| Smoothie support | Liquid-base pool + blend validation |
| Beverage-type eligibility | Auto-tagged on seed; auditable via scripts |

Ingredients are seeded in batches — review and verify entries as you use them. Full list target: ~550 names in `ingredients_to_seed.txt`.

---

## Stack

- **Database:** Supabase (Postgres) — schema in `supabase/schema.sql`
- **Backend:** FastAPI + Anthropic API (Sonnet for seeding, Haiku for combinations)
- **Frontend:** React + TypeScript + Tailwind, Vite dev proxy to API

No auth. Personal local app only.

---

## Project structure

```
beverage-recipe-app/
├── supabase/schema.sql              # Postgres schema (run in Supabase SQL editor)
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── routers/                 # ingredients, recipes, combinations
│   │   └── services/
│   │       ├── anthropic_service.py
│   │       ├── beverage_type_eligibility.py  # beverage_types + transform rules
│   │       ├── combination_service.py
│   │       └── ingredient_service.py
│   ├── scripts/
│   │   ├── seed_ingredients.py      # AI seeding → pending_review/
│   │   ├── commit_ingredients.py    # pending_review/ → Supabase (insert only)
│   │   ├── sync_pending_ingredients.py  # upsert pending_review/ by name
│   │   ├── setup_smoothie_pool.py   # curated liquid bases + tag normalization
│   │   └── audit_smoothie_eligibility.py  # audit/fix beverage_types tags
│   ├── prompts/
│   ├── ingredients_to_seed.txt      # ~550 ingredient names
│   ├── ingredients_liquid_bases.txt
│   ├── ingredients_dev_batch.txt
│   └── pending_review/              # Generated JSON (gitignored)
└── frontend/                        # React app
    └── src/pages/                   # browser, detail, edit, verification, recipes, generator
```

---

## Quick start

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your keys (see [Environment variables](#environment-variables)).

### 2. Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Run `supabase/schema.sql` in the **SQL Editor**
3. Copy **Project URL** and **service role key** into `backend/.env`

### 3. Seed and sync ingredients

```bash
# Seed locally (no Supabase needed)
python scripts/seed_ingredients.py --limit 5 --concurrency 1

# Insert new pending JSON into Supabase
python scripts/commit_ingredients.py

# Update existing rows from pending JSON (by ingredient name)
python scripts/sync_pending_ingredients.py
```

### 4. Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Test: http://localhost:8000/health → `{"status":"ok"}`  
Docs: http://localhost:8000/docs

### 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the dev server proxies `/api` to `http://127.0.0.1:8000`.

---

## Environment variables

Copy `backend/.env.example` to `backend/.env`:

| Variable | Required for | Description |
|----------|--------------|-------------|
| `ANTHROPIC_API_KEY` | Seeding + combinations | Anthropic API key |
| `SUPABASE_URL` | API + scripts | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | API + scripts | Backend + commit scripts |
| `SUPABASE_ANON_KEY` | Optional | Reserved for future frontend direct access |
| `ANTHROPIC_MODEL` | Seeding | Default: `claude-sonnet-4-6` |
| `COMBINATION_MODEL` | Generator | Default: `claude-haiku-4-5` (faster) |
| `SEED_DELAY_SECONDS` | Seeding | Delay between API calls |

**Never commit `.env`** — it is gitignored.

---

## Frontend pages

| Route | Purpose |
|-------|---------|
| `/` | Ingredient browser (filters: category, verification, liquid-base pool) |
| `/ingredients/:id` | Ingredient detail |
| `/ingredients/:id/edit` | Upgrade / verify entry (structured form) |
| `/verification` | Verification queue (sorted by recipe usage) |
| `/combinations` | AI recipe generator (anchor or health-goal mode) |
| `/recipes` | Saved recipes |
| `/recipes/new` | Manual recipe builder (500ml yield) |

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/ingredients` | List + filter (defaults to verified only) |
| GET | `/ingredients/verification-queue` | Unverified ingredients sorted by recipe usage |
| GET | `/ingredients/{id}` | Ingredient detail |
| POST | `/ingredients` | Create ingredient |
| PUT | `/ingredients/{id}` | Update / verify ingredient |
| DELETE | `/ingredients/{id}` | Soft delete |
| GET | `/recipes` | List + filter recipes |
| GET | `/recipes/{id}` | Recipe detail with joined ingredient data |
| POST | `/recipes` | Create recipe (500ml yield enforced) |
| PUT | `/recipes/{id}` | Update recipe |
| DELETE | `/recipes/{id}` | Soft delete |
| POST | `/combinations/suggest` | AI recipe generation (anchor or goal mode) |

---

## Beverage types

Supported types: `cold_press_juice`, `smoothie`, `hot_tea`, `cold_brew`, `tonic`, `infusion`, `fermented`, `decoction`.

Each ingredient gets a `beverage_types` list based on its default preparation form (e.g. pea protein → smoothie only; fresh ginger → cold-press + tonic). Ingredients outside their default form can still appear when a **preparation transform** documents the change (e.g. powder stirred in at `finish` stage).

The combination engine validates formulations per beverage type (e.g. smoothies require a liquid base ≥80ml and blend ingredients).

---

## Scripts reference

### `seed_ingredients.py`

AI-seed ingredients from `ingredients_to_seed.txt` into `pending_review/*.json`. Resumable — skips names that already have a JSON file.

```bash
python scripts/seed_ingredients.py --ingredient "Ginger (yellow/common)" --concurrency 1
python scripts/seed_ingredients.py --limit 5
python scripts/seed_ingredients.py --concurrency 3   # full batch (~550)
```

Failures log to `seed_errors.log`. A token/cost summary prints at the end.

### `commit_ingredients.py`

Insert all `pending_review/` entries into Supabase as unverified. Skips names already in the database.

```bash
python scripts/commit_ingredients.py --dry-run
python scripts/commit_ingredients.py
```

### `sync_pending_ingredients.py`

Upsert `pending_review/` JSON into Supabase **by ingredient name** — updates existing rows (e.g. after fixing `beverage_types` locally).

```bash
python scripts/sync_pending_ingredients.py --dry-run
python scripts/sync_pending_ingredients.py
```

### `setup_smoothie_pool.py`

Write curated liquid-base ingredients (milks, protein shakes, broth, functional juices) to `pending_review/` and normalize smoothie eligibility tags.

```bash
python scripts/setup_smoothie_pool.py --dry-run
python scripts/setup_smoothie_pool.py
```

### `audit_smoothie_eligibility.py`

Audit or fix `beverage_types` across all pending JSON (and optionally sync to Supabase).

```bash
python scripts/audit_smoothie_eligibility.py
python scripts/audit_smoothie_eligibility.py --fix
python scripts/audit_smoothie_eligibility.py --fix --sync
```

---

## Design principles

- **Two-tier data model:** verified / partially_verified vs unverified — never blurred in the UI
- **Conservative AI seeding:** null over guess; every claim tagged `ai_generated` until manually upgraded
- **500ml canonical yield:** all recipes standardized; scaling is display-only
- **Preparation-aware eligibility:** beverage types reflect how an ingredient is actually used, with documented transforms when needed
- **No auth, no deployment:** personal local app only
