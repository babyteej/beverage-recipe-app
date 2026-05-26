#!/usr/bin/env python3
"""
Seed ingredient entries via the Anthropic API.

Reads ingredient names from ingredients_to_seed.txt, generates structured JSON
via Claude, validates with Pydantic, and saves to pending_review/.

Does NOT require Supabase — outputs local JSON files for review first.

Usage:
  python scripts/seed_ingredients.py
  python scripts/seed_ingredients.py --limit 5
  python scripts/seed_ingredients.py --concurrency 3
  python scripts/seed_ingredients.py --ingredient "Ginger (yellow/common)"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

# Allow running from backend/ or project root
BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app.models import IngredientCreate  # noqa: E402
from app.services.anthropic_service import AnthropicService  # noqa: E402
from app.services.beverage_type_eligibility import normalize_beverage_types  # noqa: E402

load_dotenv(BACKEND_ROOT / ".env")

PENDING_DIR = BACKEND_ROOT / "pending_review"
PROMPT_FILE = BACKEND_ROOT / "prompts" / "seed_ingredient.txt"
SEED_LIST_FILE = BACKEND_ROOT / "ingredients_to_seed.txt"
ERROR_LOG = BACKEND_ROOT / "seed_errors.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "ingredient"


def load_seed_list(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Seed list not found: {path}")
    names: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        names.append(line)
    return names


def load_prompt_template() -> str:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt template not found: {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding="utf-8")


def normalize_for_validation(data: dict) -> dict:
    """Coerce null arrays and enforce seeding defaults."""
    data = dict(data)
    data["entry_source_type"] = "ai_generated"
    data["verification_status"] = "unverified"

    hp = data.get("health_properties") or {"traditional_claims": [], "evidence_based_claims": []}
    for claim in hp.get("traditional_claims", []) or []:
        claim["source_type"] = "ai_generated"
        if "source_reference" not in claim:
            claim["source_reference"] = None
    for claim in hp.get("evidence_based_claims", []) or []:
        claim["source_type"] = "ai_generated"
        if "source_reference" not in claim:
            claim["source_reference"] = None
    data["health_properties"] = hp

    list_fields = [
        "aliases", "origin", "traditions", "flavour_profile", "secondary_terpenes",
        "beverage_types", "body_systems", "active_compounds", "contraindications",
        "combination_contraindications",
    ]
    for field in list_fields:
        if data.get(field) is None:
            data[field] = []

    data = normalize_beverage_types(data, seed_name=data.get("name"))
    return data


def save_entry(name: str, data: dict) -> Path:
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PENDING_DIR / f"{slugify(name)}.json"
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out_path


def log_error(name: str, error: str) -> None:
    with ERROR_LOG.open("a", encoding="utf-8") as f:
        f.write(f"{name}\t{error}\n")


def already_seeded(name: str) -> bool:
    return (PENDING_DIR / f"{slugify(name)}.json").exists()


def seed_one(name: str, service: AnthropicService, prompt_template: str, delay: float) -> tuple[str, bool, str | None]:
    if already_seeded(name):
        logger.info("Skipping (already exists): %s", name)
        return name, True, "skipped"

    user_prompt = prompt_template + f'"{name}"'
    try:
        raw = service.complete_json(
            system="You are a conservative botanical researcher. Output only valid JSON.",
            user=user_prompt,
        )
        normalized = normalize_for_validation(raw)
        validated = IngredientCreate.model_validate(normalized)
        payload = validated.model_dump(mode="json")
        save_entry(name, payload)
        logger.info("Saved: %s", name)
        if delay > 0:
            time.sleep(delay)
        return name, True, None
    except (json.JSONDecodeError, ValidationError, KeyError, IndexError) as exc:
        msg = f"{type(exc).__name__}: {exc}"
        logger.error("Failed: %s — %s", name, msg)
        log_error(name, msg)
        return name, False, msg
    except Exception as exc:
        msg = f"{type(exc).__name__}: {exc}"
        logger.error("Failed: %s — %s", name, msg)
        log_error(name, msg)
        return name, False, msg


async def seed_one_async(
    name: str,
    service: AnthropicService,
    prompt_template: str,
    delay: float,
    semaphore: asyncio.Semaphore,
) -> tuple[str, bool, str | None]:
    if already_seeded(name):
        logger.info("Skipping (already exists): %s", name)
        return name, True, "skipped"

    async with semaphore:
        user_prompt = prompt_template + f'"{name}"'
        try:
            raw = await service.complete_json_async(
                system="You are a conservative botanical researcher. Output only valid JSON.",
                user=user_prompt,
            )
            normalized = normalize_for_validation(raw)
            validated = IngredientCreate.model_validate(normalized)
            payload = validated.model_dump(mode="json")
            save_entry(name, payload)
            logger.info("Saved: %s", name)
            if delay > 0:
                await asyncio.sleep(delay)
            return name, True, None
        except (json.JSONDecodeError, ValidationError, KeyError, IndexError) as exc:
            msg = f"{type(exc).__name__}: {exc}"
            logger.error("Failed: %s — %s", name, msg)
            log_error(name, msg)
            return name, False, msg
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            logger.error("Failed: %s — %s", name, msg)
            log_error(name, msg)
            return name, False, msg


def print_summary(results: list[tuple[str, bool, str | None]], tracker) -> None:
    successes = sum(1 for _, ok, note in results if ok and note != "skipped")
    skipped = sum(1 for _, ok, note in results if ok and note == "skipped")
    failures = sum(1 for _, ok, _ in results if not ok)

    print("\n" + "=" * 50)
    print("SEED RUN SUMMARY")
    print("=" * 50)
    print(f"  New entries saved:  {successes}")
    print(f"  Skipped (existing): {skipped}")
    print(f"  Failures:           {failures}")
    print(f"  Input tokens:       {tracker.usage.input_tokens:,}")
    print(f"  Output tokens:      {tracker.usage.output_tokens:,}")
    print(f"  Total tokens:       {tracker.usage.total_tokens:,}")
    print(f"  Estimated cost:     ${tracker.estimated_cost_usd():.4f} USD")
    if failures:
        print(f"  Error log:          {ERROR_LOG}")
    print("=" * 50)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed ingredient entries via Anthropic API")
    parser.add_argument("--limit", type=int, default=None, help="Max ingredients to process")
    parser.add_argument("--concurrency", type=int, default=3, help="Parallel API calls (default 3)")
    parser.add_argument("--delay", type=float, default=None, help="Seconds between calls (default from SEED_DELAY_SECONDS or 1)")
    parser.add_argument("--ingredient", type=str, default=None, help="Seed a single ingredient by name")
    parser.add_argument("--file", type=str, default=None, help="Path to ingredient list file (default: ingredients_to_seed.txt)")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set. Copy backend/.env.example to backend/.env and add your key.")
        sys.exit(1)

    delay = args.delay if args.delay is not None else float(os.environ.get("SEED_DELAY_SECONDS", "1"))
    prompt_template = load_prompt_template()
    service = AnthropicService()

    if args.ingredient:
        names = [args.ingredient]
    else:
        list_file = Path(args.file) if args.file else SEED_LIST_FILE
        if not list_file.is_absolute():
            list_file = BACKEND_ROOT / list_file
        names = load_seed_list(list_file)
        if args.limit:
            names = names[: args.limit]

    logger.info("Processing %d ingredient(s) with concurrency=%d, delay=%ss", len(names), args.concurrency, delay)

    results: list[tuple[str, bool, str | None]] = []

    if args.concurrency <= 1:
        for name in names:
            results.append(seed_one(name, service, prompt_template, delay))
    else:
        async def run_batch() -> None:
            semaphore = asyncio.Semaphore(args.concurrency)
            tasks = [
                seed_one_async(name, service, prompt_template, delay, semaphore)
                for name in names
            ]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

        asyncio.run(run_batch())

    print_summary(results, service.tracker)


if __name__ == "__main__":
    main()
