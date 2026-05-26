"""Ingredient API routes."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client

from app.db.supabase_client import get_supabase_client
from app.models import Ingredient, IngredientCreate, IngredientUpdate, ingredient_to_db_payload
from app.models.api import VerificationQueueItem
from app.services import ingredient_service

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


def get_db() -> Client:
    return get_supabase_client()


@router.get("/verification-queue", response_model=list[VerificationQueueItem])
def get_verification_queue(db: Annotated[Client, Depends(get_db)]):
    items = ingredient_service.verification_queue(db)
    return [
        VerificationQueueItem(
            id=item["id"],
            name=item["name"],
            category=item["category"],
            entry_confidence=item["entry_confidence"],
            usage_count=item["usage_count"],
        )
        for item in items
    ]


@router.get("", response_model=list[Ingredient])
def list_ingredients(
    db: Annotated[Client, Depends(get_db)],
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
    include_unverified: bool = Query(default=False),
):
    rows = ingredient_service.list_ingredients(
        db,
        category=category,
        subcategory=subcategory,
        exclude_subcategory=exclude_subcategory,
        terpene=terpene,
        body_system=body_system,
        beverage_type=beverage_type,
        tradition=tradition,
        rarity=rarity,
        verification_status=verification_status,
        entry_confidence=entry_confidence,
        search=search,
        include_unverified=include_unverified,
    )
    return rows


@router.get("/{ingredient_id}", response_model=Ingredient)
def get_ingredient(ingredient_id: UUID, db: Annotated[Client, Depends(get_db)]):
    row = ingredient_service.fetch_ingredient(db, ingredient_id)
    if not row:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return row


@router.post("", response_model=Ingredient, status_code=201)
def create_ingredient(body: IngredientCreate, db: Annotated[Client, Depends(get_db)]):
    payload = ingredient_to_db_payload(body)
    try:
        return ingredient_service.create_ingredient(db, payload)
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            raise HTTPException(status_code=409, detail="Ingredient name already exists") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{ingredient_id}", response_model=Ingredient)
def update_ingredient(
    ingredient_id: UUID,
    body: IngredientUpdate,
    db: Annotated[Client, Depends(get_db)],
):
    payload = body.model_dump(mode="json", exclude_unset=True)
    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")
    row = ingredient_service.update_ingredient(db, ingredient_id, payload)
    if not row:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return row


@router.delete("/{ingredient_id}", status_code=204)
def delete_ingredient(ingredient_id: UUID, db: Annotated[Client, Depends(get_db)]):
    if not ingredient_service.soft_delete_ingredient(db, ingredient_id):
        raise HTTPException(status_code=404, detail="Ingredient not found")
