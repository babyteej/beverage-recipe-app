#!/usr/bin/env python3
"""
Upsert pending_review/ JSON files into Supabase by ingredient name.

Inserts new ingredients; updates existing rows from pending JSON (e.g. beverage_types).

Usage:
  python scripts/sync_pending_ingredients.py
  python scripts/sync_pending_ingredients.py --dry-run
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Upsert pending ingredient JSON to Supabase")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    files = sorted(PENDING_DIR.glob("*.json")) if PENDING_DIR.exists() else []
    if not files:
        print(f"No JSON files in {PENDING_DIR}")
        sys.exit(0)

    payloads: list[tuple[str, dict]] = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        ingredient = IngredientCreate.model_validate(data)
        payloads.append((path.name, ingredient_to_db_payload(ingredient)))

    if args.dry_run:
        print(f"Dry run: {len(payloads)} entries validated.")
        sys.exit(0)

    client = get_supabase_client()
    inserted = 0
    updated = 0
    errors = 0

    for filename, payload in payloads:
        name = payload["name"]
        try:
            existing = client.table("ingredients").select("id").eq("name", name).execute()
            if existing.data:
                row_id = existing.data[0]["id"]
                client.table("ingredients").update(payload).eq("id", row_id).execute()
                print(f"  Updated: {name}")
                updated += 1
            else:
                client.table("ingredients").insert(payload).execute()
                print(f"  Inserted: {name}")
                inserted += 1
        except Exception as exc:
            print(f"  ERROR ({filename}): {name} — {exc}")
            errors += 1

    print("\n" + "=" * 50)
    print("SYNC SUMMARY")
    print("=" * 50)
    print(f"  Inserted: {inserted}")
    print(f"  Updated:  {updated}")
    print(f"  Errors:   {errors}")
    print("=" * 50)


if __name__ == "__main__":
    main()
