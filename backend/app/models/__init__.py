"""Pydantic models for ingredient and recipe validation."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class IngredientCategory(str, Enum):
    FRUIT = "fruit"
    VEGETABLE = "vegetable"
    ROOT = "root"
    BARK = "bark"
    FLOWER = "flower"
    MUSHROOM = "mushroom"
    HERB = "herb"
    SEED = "seed"
    RESIN = "resin"
    FERMENTED_BASE = "fermented_base"
    MINERAL = "mineral"
    OTHER = "other"


class RarityScore(str, Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very_rare"


class SourceType(str, Enum):
    AI_GENERATED = "ai_generated"
    REFERENCE_DATABASE = "reference_database"
    PRIMARY_TEXT = "primary_text"
    PERSONAL_RESEARCH = "personal_research"
    PRACTITIONER_KNOWLEDGE = "practitioner_knowledge"


class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    PARTIALLY_VERIFIED = "partially_verified"
    VERIFIED = "verified"


class EvidenceTier(str, Enum):
    TRADITIONAL_CONSENSUS = "traditional_consensus"
    PRELIMINARY_RESEARCH = "preliminary_research"
    ESTABLISHED_RESEARCH = "established_research"
    CONFLICTING_EVIDENCE = "conflicting_evidence"


class TraditionalClaim(BaseModel):
    claim: str
    tradition: str
    source_type: SourceType = SourceType.AI_GENERATED
    source_reference: str | None = None
    confidence: ConfidenceLevel


class EvidenceBasedClaim(BaseModel):
    claim: str
    evidence_tier: EvidenceTier
    source_type: SourceType = SourceType.AI_GENERATED
    source_reference: str | None = None
    confidence: ConfidenceLevel


class HealthProperties(BaseModel):
    traditional_claims: list[TraditionalClaim] = Field(default_factory=list)
    evidence_based_claims: list[EvidenceBasedClaim] = Field(default_factory=list)


class IngredientCreate(BaseModel):
    """Schema for AI-seeded and manually created ingredients."""

    name: str
    aliases: list[str] = Field(default_factory=list)
    category: IngredientCategory
    subcategory: str | None = None
    origin: list[str] = Field(default_factory=list)
    traditions: list[str] = Field(default_factory=list)

    flavour_profile: list[str] = Field(default_factory=list)
    flavour_intensity: int | None = Field(default=None, ge=1, le=5)
    primary_terpene: str | None = None
    secondary_terpenes: list[str] = Field(default_factory=list)

    beverage_types: list[str] = Field(default_factory=list)

    health_properties: HealthProperties = Field(default_factory=HealthProperties)

    body_systems: list[str] = Field(default_factory=list)
    active_compounds: list[str] = Field(default_factory=list)
    bioavailability_notes: str | None = None
    preparation_notes: str | None = None

    contraindications: list[str] = Field(default_factory=list)
    combination_contraindications: list[str] = Field(default_factory=list)
    ratio_guidance: str | None = None

    rarity_score: RarityScore | None = None
    sourcing_notes: str | None = None

    history: str | None = None
    personal_notes: str | None = None

    entry_source_type: SourceType = SourceType.AI_GENERATED
    entry_confidence: ConfidenceLevel = ConfidenceLevel.LOW
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verification_notes: str | None = None
    last_verified_at: datetime | None = None


class IngredientUpdate(BaseModel):
    """Partial update — all fields optional."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    aliases: list[str] | None = None
    category: IngredientCategory | None = None
    subcategory: str | None = None
    origin: list[str] | None = None
    traditions: list[str] | None = None
    flavour_profile: list[str] | None = None
    flavour_intensity: int | None = Field(default=None, ge=1, le=5)
    primary_terpene: str | None = None
    secondary_terpenes: list[str] | None = None
    beverage_types: list[str] | None = None
    health_properties: HealthProperties | None = None
    body_systems: list[str] | None = None
    active_compounds: list[str] | None = None
    bioavailability_notes: str | None = None
    preparation_notes: str | None = None
    contraindications: list[str] | None = None
    combination_contraindications: list[str] | None = None
    ratio_guidance: str | None = None
    rarity_score: RarityScore | None = None
    sourcing_notes: str | None = None
    history: str | None = None
    personal_notes: str | None = None
    entry_source_type: SourceType | None = None
    entry_confidence: ConfidenceLevel | None = None
    verification_status: VerificationStatus | None = None
    verification_notes: str | None = None
    last_verified_at: datetime | None = None


class Ingredient(IngredientCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class RecipeIngredient(BaseModel):
    ingredient_id: UUID
    amount_metric: float
    unit_metric: str
    amount_imperial: float
    unit_imperial: str
    preparation: str | None = None
    stage: str
    notes: str | None = None


class RecipeInstruction(BaseModel):
    step: int
    action: str
    duration_seconds: int | None = None
    equipment: list[str] = Field(default_factory=list)
    tip: str | None = None


class SensoryProfile(BaseModel):
    color: str | None = None
    aroma: str | None = None
    mouthfeel: str | None = None
    primary_taste: str | None = None


class ContextualFit(BaseModel):
    time_of_day: list[str] = Field(default_factory=list)
    season: list[str] = Field(default_factory=list)
    physiological_state: list[str] = Field(default_factory=list)


class RecipeCreate(BaseModel):
    name: str
    description: str | None = None
    beverage_type: str | None = None
    yield_ml: int = 500
    preparation_time_minutes: int | None = None
    total_time_minutes: int | None = None
    ingredients: list[RecipeIngredient]
    instructions: list[RecipeInstruction]
    equipment_required: list[str] = Field(default_factory=list)
    health_goals: list[str] = Field(default_factory=list)
    body_systems_targeted: list[str] = Field(default_factory=list)
    evidence_tier: EvidenceTier | None = None
    terpene_profile: list[str] = Field(default_factory=list)
    flavour_balance_notes: str | None = None
    sensory_profile: SensoryProfile = Field(default_factory=SensoryProfile)
    contextual_fit: ContextualFit = Field(default_factory=ContextualFit)
    contraindications: list[str] = Field(default_factory=list)
    origin_story: str | None = None
    tags: list[str] = Field(default_factory=list)
    personal_rating: int | None = Field(default=None, ge=1, le=5)
    notes: str | None = None


class Recipe(RecipeCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


def ingredient_to_db_payload(ingredient: IngredientCreate | Ingredient) -> dict[str, Any]:
    """Convert a Pydantic ingredient model to a Supabase-compatible dict."""
    data = ingredient.model_dump(mode="json", exclude_none=False)
    if isinstance(data.get("health_properties"), dict):
        pass  # already serialized
    return data
