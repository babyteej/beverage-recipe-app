"""Database helpers for recipes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from supabase import Client

from app.services.ingredient_service import fetch_ingredients_by_ids


def _active_query(client: Client):
    return client.table("recipes").select("*").is_("deleted_at", "null")


def list_recipes(
    client: Client,
    *,
    health_goal: str | None = None,
    body_system: str | None = None,
    beverage_type: str | None = None,
    tag: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    query = _active_query(client)

    if health_goal:
        query = query.contains("health_goals", [health_goal])
    if body_system:
        query = query.contains("body_systems_targeted", [body_system])
    if beverage_type:
        query = query.eq("beverage_type", beverage_type)
    if tag:
        query = query.contains("tags", [tag])
    if search:
        query = query.ilike("name", f"%{search}%")

    result = query.order("name").execute()
    recipes = result.data or []
    return [_annotate_data_quality(client, recipe) for recipe in recipes]


def _annotate_data_quality(client: Client, recipe: dict[str, Any]) -> dict[str, Any]:
    ing_ids = [UUID(str(i["ingredient_id"])) for i in recipe.get("ingredients") or []]
    ingredients = fetch_ingredients_by_ids(client, ing_ids)
    unverified = any(i.get("verification_status") == "unverified" for i in ingredients)
    recipe["has_unverified_ingredients"] = unverified
    return recipe


def fetch_recipe(client: Client, recipe_id: UUID) -> dict[str, Any] | None:
    result = _active_query(client).eq("id", str(recipe_id)).execute()
    rows = result.data or []
    if not rows:
        return None
    return enrich_recipe_detail(client, rows[0])


def enrich_recipe_detail(client: Client, recipe: dict[str, Any]) -> dict[str, Any]:
    ing_ids = [UUID(str(i["ingredient_id"])) for i in recipe.get("ingredients") or []]
    ingredients = fetch_ingredients_by_ids(client, ing_ids)
    by_id = {str(i["id"]): i for i in ingredients}

    enriched = []
    has_unverified = False
    for item in recipe.get("ingredients") or []:
        meta = by_id.get(str(item["ingredient_id"]), {})
        if meta.get("verification_status") == "unverified":
            has_unverified = True
        enriched.append(
            {
                **item,
                "ingredient_name": meta.get("name"),
                "verification_status": meta.get("verification_status"),
            }
        )

    recipe = dict(recipe)
    recipe["ingredients"] = enriched
    recipe["has_unverified_ingredients"] = has_unverified
    return recipe


def create_recipe(client: Client, payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    payload.setdefault("yield_ml", 500)
    result = client.table("recipes").insert(payload).execute()
    return enrich_recipe_detail(client, result.data[0])


def update_recipe(client: Client, recipe_id: UUID, payload: dict[str, Any]) -> dict[str, Any] | None:
    result = (
        client.table("recipes")
        .update(payload)
        .eq("id", str(recipe_id))
        .is_("deleted_at", "null")
        .execute()
    )
    rows = result.data or []
    if not rows:
        return None
    return enrich_recipe_detail(client, rows[0])


def soft_delete_recipe(client: Client, recipe_id: UUID) -> bool:
    result = (
        client.table("recipes")
        .update({"deleted_at": datetime.now(timezone.utc).isoformat()})
        .eq("id", str(recipe_id))
        .is_("deleted_at", "null")
        .execute()
    )
    return bool(result.data)
