"""Recipe API routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import Client

from app.db.supabase_client import get_supabase_client
from app.models import RecipeCreate
from app.models.api import RecipeDetailResponse
from app.services import recipe_service

router = APIRouter(prefix="/recipes", tags=["recipes"])


class RecipeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    beverage_type: str | None = None
    yield_ml: int | None = None
    preparation_time_minutes: int | None = None
    total_time_minutes: int | None = None
    ingredients: list | None = None
    instructions: list | None = None
    equipment_required: list[str] | None = None
    health_goals: list[str] | None = None
    body_systems_targeted: list[str] | None = None
    evidence_tier: str | None = None
    terpene_profile: list[str] | None = None
    flavour_balance_notes: str | None = None
    sensory_profile: dict | None = None
    contextual_fit: dict | None = None
    contraindications: list[str] | None = None
    origin_story: str | None = None
    tags: list[str] | None = None
    personal_rating: int | None = None
    notes: str | None = None


def get_db() -> Client:
    return get_supabase_client()


@router.get("")
def list_recipes(
    db: Annotated[Client, Depends(get_db)],
    health_goal: str | None = None,
    body_system: str | None = None,
    beverage_type: str | None = None,
    tag: str | None = None,
    search: str | None = None,
):
    return recipe_service.list_recipes(
        db,
        health_goal=health_goal,
        body_system=body_system,
        beverage_type=beverage_type,
        tag=tag,
        search=search,
    )


@router.get("/{recipe_id}", response_model=RecipeDetailResponse)
def get_recipe(recipe_id: UUID, db: Annotated[Client, Depends(get_db)]):
    row = recipe_service.fetch_recipe(db, recipe_id)
    if not row:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return row


@router.post("", response_model=RecipeDetailResponse, status_code=201)
def create_recipe(body: RecipeCreate, db: Annotated[Client, Depends(get_db)]):
    payload = body.model_dump(mode="json")
    if payload.get("yield_ml") != 500:
        raise HTTPException(status_code=400, detail="yield_ml must be 500")
    return recipe_service.create_recipe(db, payload)


@router.put("/{recipe_id}", response_model=RecipeDetailResponse)
def update_recipe(recipe_id: UUID, body: RecipeUpdate, db: Annotated[Client, Depends(get_db)]):
    payload = body.model_dump(mode="json", exclude_unset=True)
    if "yield_ml" in payload and payload["yield_ml"] != 500:
        raise HTTPException(status_code=400, detail="yield_ml must be 500")
    row = recipe_service.update_recipe(db, recipe_id, payload)
    if not row:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return row


@router.delete("/{recipe_id}", status_code=204)
def delete_recipe(recipe_id: UUID, db: Annotated[Client, Depends(get_db)]):
    if not recipe_service.soft_delete_recipe(db, recipe_id):
        raise HTTPException(status_code=404, detail="Recipe not found")
