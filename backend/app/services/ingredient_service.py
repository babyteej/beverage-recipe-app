"""Database helpers for ingredients."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from supabase import Client

VERIFIED_STATUSES = ("verified", "partially_verified")


def _active_query(client: Client, table: str):
    return client.table(table).select("*").is_("deleted_at", "null")


def fetch_ingredient(client: Client, ingredient_id: UUID) -> dict[str, Any] | None:
    result = _active_query(client, "ingredients").eq("id", str(ingredient_id)).execute()
    rows = result.data or []
    return rows[0] if rows else None


def fetch_ingredients_by_ids(client: Client, ids: list[UUID]) -> list[dict[str, Any]]:
    if not ids:
        return []
    str_ids = [str(i) for i in ids]
    result = _active_query(client, "ingredients").in_("id", str_ids).execute()
    return result.data or []


def list_ingredients(
    client: Client,
    *,
    category: str | None = None,
    subcategory: str | None = None,
    exclude_subcategory: str | None = None,
    terpene: str | None = None,
    body_system: str | None = None,
    beverage_type: str | None = None,
    tradition: str | None = None,
    rarity: str | None = None,
    verification_status: str | None = None,
    entry_confidence: str | None = None,
    search: str | None = None,
    include_unverified: bool = False,
) -> list[dict[str, Any]]:
    query = _active_query(client, "ingredients")

    if include_unverified:
        if verification_status:
            query = query.eq("verification_status", verification_status)
    else:
        if verification_status:
            if verification_status not in VERIFIED_STATUSES:
                return []
            query = query.eq("verification_status", verification_status)
        else:
            query = query.in_("verification_status", list(VERIFIED_STATUSES))

    if category:
        query = query.eq("category", category)
    if subcategory:
        query = query.eq("subcategory", subcategory)
    if exclude_subcategory:
        query = query.or_(f"subcategory.is.null,subcategory.neq.{exclude_subcategory}")
    if terpene:
        query = query.eq("primary_terpene", terpene)
    if body_system:
        query = query.contains("body_systems", [body_system])
    if beverage_type:
        query = query.contains("beverage_types", [beverage_type])
    if tradition:
        query = query.contains("traditions", [tradition])
    if rarity:
        query = query.eq("rarity_score", rarity)
    if entry_confidence:
        query = query.eq("entry_confidence", entry_confidence)
    if search:
        query = query.ilike("name", f"%{search}%")

    result = query.order("name").execute()
    return result.data or []


def list_liquid_base_ingredients(
    client: Client,
    *,
    include_unverified: bool = False,
) -> list[dict[str, Any]]:
    """Ingredients tagged subcategory=liquid_base for smoothie liquid_base stage."""
    query = _active_query(client, "ingredients").eq("subcategory", "liquid_base")

    if include_unverified:
        pass
    else:
        query = query.in_("verification_status", list(VERIFIED_STATUSES))

    result = query.order("name").execute()
    return result.data or []


def create_ingredient(client: Client, payload: dict[str, Any]) -> dict[str, Any]:
    result = client.table("ingredients").insert(payload).execute()
    return result.data[0]


def update_ingredient(
    client: Client, ingredient_id: UUID, payload: dict[str, Any]
) -> dict[str, Any] | None:
    verification_fields = {
        "verification_status",
        "entry_source_type",
        "entry_confidence",
        "verification_notes",
        "health_properties",
    }
    if verification_fields.intersection(payload.keys()) and "last_verified_at" not in payload:
        payload["last_verified_at"] = datetime.now(timezone.utc).isoformat()

    result = (
        client.table("ingredients")
        .update(payload)
        .eq("id", str(ingredient_id))
        .is_("deleted_at", "null")
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def soft_delete_ingredient(client: Client, ingredient_id: UUID) -> bool:
    result = (
        client.table("ingredients")
        .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", str(ingredient_id))
        .is_("deleted_at", "null")
        .execute()
    )
    return bool(result.data)


def compute_ingredient_usage_counts(client: Client) -> dict[str, int]:
    """Count how often each ingredient_id appears in saved recipes."""
    result = client.table("recipes").select("ingredients").is_("deleted_at", "null").execute()
    counts: dict[str, int] = {}
    for recipe in result.data or []:
        seen_in_recipe: set[str] = set()
        for item in recipe.get("ingredients") or []:
            ing_id = str(item.get("ingredient_id", ""))
            if ing_id and ing_id not in seen_in_recipe:
                counts[ing_id] = counts.get(ing_id, 0) + 1
                seen_in_recipe.add(ing_id)
    return counts


def verification_queue(client: Client) -> list[dict[str, Any]]:
    usage = compute_ingredient_usage_counts(client)
    result = (
        _active_query(client, "ingredients")
        .eq("verification_status", "unverified")
        .execute()
    )
    items = result.data or []
    for item in items:
        item["usage_count"] = usage.get(str(item["id"]), 0)
    items.sort(key=lambda x: (-x["usage_count"], x["name"].lower()))
    return items
