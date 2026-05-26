#!/usr/bin/env python3
"""
Audit and fix beverage_types tags across pending_review/ (and optionally Supabase).

Usage:
  python scripts/audit_smoothie_eligibility.py
  python scripts/audit_smoothie_eligibility.py --fix
  python scripts/audit_smoothie_eligibility.py --fix --sync
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.beverage_type_eligibility import (  # noqa: E402
    compute_eligible_beverage_types,
    ineligibility_notes,
    normalize_beverage_types,
)

PENDING_DIR = BACKEND_ROOT / "pending_review"


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "ingredient"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit smoothie beverage_types in pending_review/")
    parser.add_argument("--fix", action="store_true", help="Rewrite JSON files with corrected tags")
    parser.add_argument("--sync", action="store_true", help="Run sync_pending_ingredients.py after --fix")
    args = parser.parse_args()

    if not PENDING_DIR.exists():
        print(f"No {PENDING_DIR}")
        sys.exit(0)

    excluded_smoothie: list[tuple[str, str]] = []
    included: list[str] = []
    mismatches: list[tuple[str, list[str], list[str]]] = []
    liquid_bases: list[str] = []
    fixed = 0

    for path in sorted(PENDING_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        name = data.get("name") or path.stem
        slug = path.stem
        before = sorted(data.get("beverage_types") or [])

        if data.get("subcategory") == "liquid_base":
            liquid_bases.append(name)

        eligible = sorted(compute_eligible_beverage_types(data, slug=slug))
        normalized = normalize_beverage_types(dict(data), slug=slug)
        after = list(normalized.get("beverage_types") or [])

        if before != eligible:
            mismatches.append((name, before, eligible))
        if "smoothie" not in eligible:
            reason = ineligibility_notes(data, "smoothie", slug=slug) or "not smoothie-eligible"
            excluded_smoothie.append((name, reason))
        elif "smoothie" in after:
            included.append(name)

        if before != after:
            if args.fix:
                path.write_text(
                    json.dumps(normalized, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                print(f"  Fixed: {name}  {before} -> {after}")
            else:
                print(f"  Would fix: {name}  {before} -> {after}")
            fixed += 1

    print("\n" + "=" * 50)
    print("BEVERAGE TYPE ELIGIBILITY AUDIT")
    print("=" * 50)
    print(f"  Liquid bases:           {len(liquid_bases)}")
    print(f"  Smoothie-eligible:      {len(included)}")
    print(f"  Smoothie-ineligible:    {len(excluded_smoothie)}")
    print(f"  Tag mismatches found:   {len(mismatches)}")
    print(f"  Files fixed:            {fixed}")
    if mismatches:
        print("\n  Corrected beverage_types (before -> eligible):")
        for name, before, eligible in mismatches[:20]:
            print(f"    - {name}: {before} -> {eligible}")
        if len(mismatches) > 20:
            print(f"    ... and {len(mismatches) - 20} more")
    if excluded_smoothie:
        print("\n  Excluded from smoothie:")
        for name, reason in excluded_smoothie:
            print(f"    - {name}: {reason}")
    if not args.fix and fixed:
        print("\n  Re-run with --fix to apply changes.")
    print("=" * 50)

    if args.sync:
        if not args.fix:
            print("ERROR: --sync requires --fix")
            sys.exit(1)
        subprocess.run(
            [sys.executable, str(BACKEND_ROOT / "scripts" / "sync_pending_ingredients.py")],
            check=True,
        )


if __name__ == "__main__":
    main()
