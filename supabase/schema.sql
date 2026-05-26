-- Beverage Recipe & Knowledge Base — Database Schema
-- Run this in the Supabase SQL Editor after creating your project.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE ingredient_category AS ENUM (
  'fruit', 'vegetable', 'root', 'bark', 'flower', 'mushroom',
  'herb', 'seed', 'resin', 'fermented_base', 'mineral', 'other'
);

CREATE TYPE rarity_score AS ENUM (
  'common', 'uncommon', 'rare', 'very_rare'
);

CREATE TYPE source_type AS ENUM (
  'ai_generated',
  'reference_database',
  'primary_text',
  'personal_research',
  'practitioner_knowledge'
);

CREATE TYPE confidence_level AS ENUM (
  'low', 'medium', 'high'
);

CREATE TYPE verification_status AS ENUM (
  'unverified', 'partially_verified', 'verified'
);

CREATE TYPE evidence_tier AS ENUM (
  'traditional_consensus',
  'preliminary_research',
  'established_research',
  'conflicting_evidence'
);

-- ============================================================
-- INGREDIENTS
-- ============================================================

CREATE TABLE ingredients (
  id                            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                          TEXT NOT NULL UNIQUE,
  aliases                       TEXT[] DEFAULT '{}',
  category                      ingredient_category NOT NULL,
  subcategory                   TEXT,
  origin                        TEXT[] DEFAULT '{}',
  traditions                    TEXT[] DEFAULT '{}',

  flavour_profile               TEXT[] DEFAULT '{}',
  flavour_intensity             INTEGER CHECK (flavour_intensity BETWEEN 1 AND 5),
  primary_terpene               TEXT,
  secondary_terpenes            TEXT[] DEFAULT '{}',

  beverage_types                TEXT[] DEFAULT '{}',

  health_properties             JSONB NOT NULL DEFAULT '{"traditional_claims": [], "evidence_based_claims": []}'::jsonb,

  body_systems                  TEXT[] DEFAULT '{}',
  active_compounds              TEXT[] DEFAULT '{}',
  bioavailability_notes         TEXT,
  preparation_notes             TEXT,

  contraindications             TEXT[] DEFAULT '{}',
  combination_contraindications TEXT[] DEFAULT '{}',
  ratio_guidance                TEXT,

  rarity_score                  rarity_score,
  sourcing_notes                TEXT,

  history                       TEXT,
  personal_notes                TEXT,

  entry_source_type             source_type NOT NULL DEFAULT 'ai_generated',
  entry_confidence              confidence_level NOT NULL DEFAULT 'low',
  verification_status           verification_status NOT NULL DEFAULT 'unverified',
  verification_notes            TEXT,
  last_verified_at              TIMESTAMPTZ,

  created_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                    TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at                    TIMESTAMPTZ
);

-- ============================================================
-- RECIPES
-- ============================================================

CREATE TABLE recipes (
  id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name                        TEXT NOT NULL,
  description                 TEXT,
  beverage_type               TEXT,

  yield_ml                    INTEGER NOT NULL DEFAULT 500 CHECK (yield_ml > 0),

  preparation_time_minutes    INTEGER,
  total_time_minutes          INTEGER,

  ingredients                 JSONB NOT NULL DEFAULT '[]'::jsonb,
  instructions                JSONB NOT NULL DEFAULT '[]'::jsonb,

  equipment_required          TEXT[] DEFAULT '{}',

  health_goals                TEXT[] DEFAULT '{}',
  body_systems_targeted       TEXT[] DEFAULT '{}',
  evidence_tier               evidence_tier,

  terpene_profile             TEXT[] DEFAULT '{}',
  flavour_balance_notes       TEXT,
  sensory_profile             JSONB DEFAULT '{}'::jsonb,
  contextual_fit              JSONB DEFAULT '{}'::jsonb,

  contraindications           TEXT[] DEFAULT '{}',
  origin_story                TEXT,
  tags                        TEXT[] DEFAULT '{}',
  personal_rating             INTEGER CHECK (personal_rating BETWEEN 1 AND 5),
  notes                       TEXT,

  created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at                  TIMESTAMPTZ
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_ingredients_category ON ingredients (category);
CREATE INDEX idx_ingredients_primary_terpene ON ingredients (primary_terpene);
CREATE INDEX idx_ingredients_body_systems ON ingredients USING GIN (body_systems);
CREATE INDEX idx_ingredients_beverage_types ON ingredients USING GIN (beverage_types);
CREATE INDEX idx_ingredients_verification_status ON ingredients (verification_status);
CREATE INDEX idx_ingredients_active ON ingredients (deleted_at) WHERE deleted_at IS NULL;

CREATE INDEX idx_recipes_health_goals ON recipes USING GIN (health_goals);
CREATE INDEX idx_recipes_body_systems_targeted ON recipes USING GIN (body_systems_targeted);
CREATE INDEX idx_recipes_active ON recipes (deleted_at) WHERE deleted_at IS NULL;

-- ============================================================
-- UPDATED_AT TRIGGER
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ingredients_updated_at
  BEFORE UPDATE ON ingredients
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_recipes_updated_at
  BEFORE UPDATE ON recipes
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
