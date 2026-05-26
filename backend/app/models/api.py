"""Shared API request/response models."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models import (
    ContextualFit,
    RecipeCreate,
    RecipeIngredient,
    RecipeInstruction,
    SensoryProfile,
)


class CombinationConstraints(BaseModel):
    beverage_type: str | None = None
    time_of_day: str | None = None
    season: str | None = None
    equipment_available: list[str] = Field(default_factory=list)
    exclude_ingredients: list[UUID] = Field(default_factory=list)
    max_ingredients: int = Field(default=7, ge=3, le=12)


class CombinationSuggestRequest(BaseModel):
    mode: Literal["anchor", "goal"]
    anchor_ingredient_ids: list[UUID] | None = None
    health_goals: list[str] | None = None
    constraints: CombinationConstraints = Field(default_factory=CombinationConstraints)
    include_unverified: bool = False


class SuggestedFormulation(BaseModel):
    name: str
    description: str | None = None
    beverage_type: str
    yield_ml: int = 500
    preparation_time_minutes: int | None = None
    total_time_minutes: int | None = None
    ingredients: list[RecipeIngredient]
    instructions: list[RecipeInstruction]
    equipment_required: list[str] = Field(default_factory=list)
    health_goals: list[str] = Field(default_factory=list)
    body_systems_targeted: list[str] = Field(default_factory=list)
    evidence_tier: str | None = None
    terpene_profile: list[str] = Field(default_factory=list)
    flavour_balance_notes: str | None = None
    sensory_profile: SensoryProfile = Field(default_factory=SensoryProfile)
    contextual_fit: ContextualFit = Field(default_factory=ContextualFit)
    contraindications: list[str] = Field(default_factory=list)
    reasoning: str
    contains_unverified_ingredients: bool = False


class CombinationSuggestResponse(BaseModel):
    formulations: list[SuggestedFormulation]
    candidate_pool_size: int
    exploratory_mode: bool = False


class CombinationErrorResponse(BaseModel):
    error: str
    suggestion: str | None = None
    candidate_pool_size: int = 0


class VerificationQueueItem(BaseModel):
    id: UUID
    name: str
    category: str
    entry_confidence: str
    usage_count: int


class EnrichedRecipeIngredient(RecipeIngredient):
    ingredient_name: str | None = None
    verification_status: str | None = None


class RecipeDetailResponse(RecipeCreate):
    id: UUID
    created_at: str
    updated_at: str
    ingredients: list[EnrichedRecipeIngredient]
    has_unverified_ingredients: bool = False
