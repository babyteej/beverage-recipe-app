#!/usr/bin/env python3
"""
Commit pending_review/ JSON files into Supabase.

Requires a Supabase project with schema.sql already applied.
Uses SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY from .env.

Usage:
  python scripts/commit_ingredients.py
  python scripts/commit_ingredients.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.models import IngredientCreate, ingredient_to_db_payload  # noqa: E402
from app.db.supabase_client import get_supabase_client  # noqa: E402

load_dotenv(BACKEND_ROOT / ".env")

PENDING_DIR = BACKEND_ROOT / "pending_review"


def load_pending_files() -> list[Path]:
    if not PENDING_DIR.exists():
        return []
    return sorted(PENDING_DIR.glob("*.json"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Commit pending ingredient JSON to Supabase")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, do not insert")
    args = parser.parse_args()

    files = load_pending_files()
    if not files:
        print(f"No JSON files found in {PENDING_DIR}")
        print("Run seed_ingredients.py first.")
        sys.exit(0)

    print(f"Found {len(files)} file(s) in pending_review/")

    validated: list[dict] = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        ingredient = IngredientCreate.model_validate(data)
        payload = ingredient_to_db_payload(ingredient)
        validated.append(payload)

    if args.dry_run:
        print(f"Dry run: {len(validated)} entries validated successfully. No database writes.")
        sys.exit(0)

    client = get_supabase_client()
    inserted = 0
    skipped = 0
    errors = 0

    for payload in validated:
        name = payload["name"]
        try:
            existing = client.table("ingredients").select("id").eq("name", name).execute()
            if existing.data:
                print(f"  Skip (exists): {name}")
                skipped += 1
                continue

            client.table("ingredients").insert(payload).execute()
            print(f"  Inserted: {name}")
            inserted += 1
        except Exception as exc:
            print(f"  ERROR: {name} — {exc}")
            errors += 1

    print("\n" + "=" * 50)
    print("COMMIT SUMMARY")
    print("=" * 50)
    print(f"  Inserted: {inserted}")
    print(f"  Skipped:  {skipped}")
    print(f"  Errors:   {errors}")
    print("=" * 50)


if __name__ == "__main__":
    main()
