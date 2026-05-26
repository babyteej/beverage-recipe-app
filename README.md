# Beverage Recipe & Knowledge Base

A personal recipe and ingredient knowledge base for health-and-wellness beverages — juices, teas, tonics, infusions, cold brews, fermented drinks, and decoctions.

The database is the product. AI-seeded entries live in an **unverified pool** until manually upgraded; the UI keeps verified and unverified data strictly separate.

---

## Project structure

```
beverage-recipe-app/
├── supabase/schema.sql          # Postgres schema (run in Supabase SQL editor)
├── backend/
│   ├── app/                     # FastAPI application (step 3)
│   ├── scripts/
│   │   ├── seed_ingredients.py  # AI seeding → pending_review/
│   │   └── commit_ingredients.py # pending_review/ → Supabase
│   ├── prompts/seed_ingredient.txt
│   ├── ingredients_to_seed.txt  # ~550 ingredients
│   └── pending_review/          # Generated JSON awaiting commit
└── frontend/                    # React + Tailwind (step 4)
```

---

## Build progress

| Step | Status | Needs Supabase? |
|------|--------|-----------------|
| 1. Database schema | Done | No (file only) |
| 2. Seeding scripts | Done | No (writes local JSON) |
| 3. FastAPI backend + combination engine | Done | **Yes** |
| 4. React frontend | Done | Yes (via API proxy) |

---

## API endpoints

With Supabase configured, start the server:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs

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

## Setup — Phase 1 (no Supabase needed)

You can seed ingredients locally before creating a Supabase project.

### 1. Backend dependencies

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your **Anthropic API key** (required for seeding):

```
ANTHROPIC_API_KEY=sk-ant-...
```

Supabase keys can wait until Phase 2.

### 3. Test seeding (start small)

```bash
# Seed a single ingredient to verify everything works
python scripts/seed_ingredients.py --ingredient "Ginger (yellow/common)" --concurrency 1

# Or seed the first 5 from the list
python scripts/seed_ingredients.py --limit 5 --concurrency 1
```

Output lands in `backend/pending_review/*.json`. Review a file before running the full batch.

### 4. Full batch (optional, ~550 ingredients)

```bash
python scripts/seed_ingredients.py --concurrency 3
```

The script is resumable — it skips ingredients that already have a JSON file in `pending_review/`. Failures are logged to `seed_errors.log`. A cost summary prints at the end.

---

## Setup — Phase 2 (Supabase required)

**Create your Supabase project when you're ready to commit seeded data or run the API.**

### 1. Create a Supabase project

1. Go to [supabase.com](https://supabase.com) → **New project**
2. Choose a region close to you
3. Save your database password securely
4. Wait for the project to finish provisioning (~2 minutes)

### 2. Run the schema

1. In Supabase: **SQL Editor** → **New query**
2. Paste the contents of `supabase/schema.sql`
3. Click **Run**

### 3. Copy API keys to `.env`

In Supabase: **Project Settings → API**

```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...   # for commit script + backend
SUPABASE_ANON_KEY=eyJ...           # for frontend (later)
```

### 4. Commit seeded ingredients

```bash
# Validate without writing
python scripts/commit_ingredients.py --dry-run

# Insert all pending_review/ entries as unverified
python scripts/commit_ingredients.py
```

### 5. Start the API

```bash
uvicorn app.main:app --reload --port 8000
```

Test: http://localhost:8000/health → `{"status":"ok"}`

---

## ⏸ Supabase checkpoint — you are here

The backend is built. To use it you need to:

1. **Create a Supabase project** at [supabase.com](https://supabase.com)
2. **Run** `supabase/schema.sql` in the SQL Editor
3. **Add** `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` to `backend/.env`
4. **Commit** seeded ingredients: `python scripts/commit_ingredients.py`
5. **Start** the API: `uvicorn app.main:app --reload --port 8000`

You can keep seeding more ingredients locally while setting up Supabase.

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the dev server proxies API requests to the backend at `:8000`.

Make sure the backend is running:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

---

## Design principles

- **Two-tier data model:** verified/partially_verified vs unverified — never blurred in the UI
- **Conservative AI seeding:** null over guess; every claim tagged `ai_generated` until manually upgraded
- **500ml canonical yield:** all recipes standardized; scaling is display-only
- **No auth, no deployment:** personal local app only
