export type VerificationStatus = 'unverified' | 'partially_verified' | 'verified'
export type SourceType = 'ai_generated' | 'reference_database' | 'primary_text' | 'personal_research' | 'practitioner_knowledge'
export type ConfidenceLevel = 'low' | 'medium' | 'high'

export interface TraditionalClaim {
  claim: string
  tradition: string
  source_type: SourceType
  source_reference: string | null
  confidence: ConfidenceLevel
}

export interface EvidenceBasedClaim {
  claim: string
  evidence_tier: string
  source_type: SourceType
  source_reference: string | null
  confidence: ConfidenceLevel
}

export interface HealthProperties {
  traditional_claims: TraditionalClaim[]
  evidence_based_claims: EvidenceBasedClaim[]
}

export interface Ingredient {
  id: string
  name: string
  aliases: string[]
  category: string
  subcategory: string | null
  origin: string[]
  traditions: string[]
  flavour_profile: string[]
  flavour_intensity: number | null
  primary_terpene: string | null
  secondary_terpenes: string[]
  beverage_types: string[]
  health_properties: HealthProperties
  body_systems: string[]
  active_compounds: string[]
  bioavailability_notes: string | null
  preparation_notes: string | null
  contraindications: string[]
  combination_contraindications: string[]
  ratio_guidance: string | null
  rarity_score: string | null
  sourcing_notes: string | null
  history: string | null
  personal_notes: string | null
  entry_source_type: SourceType
  entry_confidence: ConfidenceLevel
  verification_status: VerificationStatus
  verification_notes: string | null
  last_verified_at: string | null
  created_at: string
  updated_at: string
}

export interface VerificationQueueItem {
  id: string
  name: string
  category: string
  entry_confidence: ConfidenceLevel
  usage_count: number
}

export interface RecipeIngredient {
  ingredient_id: string
  amount_metric: number
  unit_metric: string
  amount_imperial: number
  unit_imperial: string
  preparation?: string | null
  stage: string
  notes?: string | null
  ingredient_name?: string | null
  verification_status?: VerificationStatus | null
}

export interface RecipeInstruction {
  step: number
  action: string
  duration_seconds?: number | null
  equipment: string[]
  tip?: string | null
}

export interface Recipe {
  id: string
  name: string
  description: string | null
  beverage_type: string | null
  yield_ml: number
  preparation_time_minutes: number | null
  total_time_minutes: number | null
  ingredients: RecipeIngredient[]
  instructions: RecipeInstruction[]
  equipment_required: string[]
  health_goals: string[]
  body_systems_targeted: string[]
  evidence_tier: string | null
  terpene_profile: string[]
  flavour_balance_notes: string | null
  sensory_profile: Record<string, string | undefined>
  contextual_fit: Record<string, string[]>
  contraindications: string[]
  origin_story: string | null
  tags: string[]
  personal_rating: number | null
  notes: string | null
  has_unverified_ingredients?: boolean
  created_at: string
  updated_at: string
}

export interface SuggestedFormulation {
  name: string
  description: string | null
  beverage_type: string
  yield_ml: number
  preparation_time_minutes: number | null
  total_time_minutes: number | null
  ingredients: RecipeIngredient[]
  instructions: RecipeInstruction[]
  equipment_required: string[]
  health_goals: string[]
  body_systems_targeted: string[]
  evidence_tier: string | null
  terpene_profile: string[]
  flavour_balance_notes: string | null
  sensory_profile: Record<string, string | undefined>
  contextual_fit: Record<string, string[]>
  contraindications: string[]
  reasoning: string
  contains_unverified_ingredients: boolean
}

export interface CombinationRequest {
  mode: 'anchor' | 'goal'
  anchor_ingredient_ids?: string[]
  health_goals?: string[]
  constraints?: {
    beverage_type?: string
    time_of_day?: string
    season?: string
    equipment_available?: string[]
    exclude_ingredients?: string[]
    max_ingredients?: number
  }
  include_unverified?: boolean
}

export const CATEGORIES = [
  'fruit', 'vegetable', 'root', 'bark', 'flower', 'mushroom',
  'herb', 'seed', 'resin', 'fermented_base', 'mineral', 'other',
] as const

export const BODY_SYSTEMS = [
  'gut', 'liver', 'nervous_system', 'immune', 'endocrine',
  'cardiovascular', 'skin', 'lymphatic', 'respiratory',
  'musculoskeletal', 'reproductive',
] as const

export const BEVERAGE_TYPES = [
  'cold_press_juice', 'smoothie', 'hot_tea', 'cold_brew', 'tonic', 'infusion', 'fermented', 'decoction',
] as const

/** Ingredient browser pool presets (maps to API subcategory filters). */
export const INGREDIENT_POOLS = [
  { value: '', label: 'All ingredients' },
  { value: 'liquid_base', label: 'Liquid bases' },
  { value: 'blend', label: 'Blend ingredients' },
] as const

export type IngredientPoolFilter = (typeof INGREDIENT_POOLS)[number]['value']

export const LIQUID_BASE_SUBCATEGORY = 'liquid_base'

export const TERPENES = [
  'linalool', 'limonene', 'eugenol', 'bisabolol', 'geraniol', 'pinene', 'myrcene', 'caryophyllene', 'other',
] as const

export const STAGES = ['liquid_base', 'blend', 'press', 'steep', 'garnish', 'finish', 'ferment'] as const

export const STAGE_LABELS: Record<string, string> = {
  liquid_base: 'Liquid base',
  blend: 'Blend',
  press: 'Press',
  steep: 'Steep',
  garnish: 'Garnish',
  finish: 'Finish',
  ferment: 'Ferment',
}

export function stagesForBeverageType(beverageType: string): readonly string[] {
  if (beverageType === 'smoothie') {
    return ['liquid_base', 'blend', 'garnish', 'finish']
  }
  if (beverageType === 'cold_press_juice') {
    return ['press', 'garnish', 'finish']
  }
  if (beverageType === 'fermented') {
    return ['ferment', 'garnish', 'finish']
  }
  if (beverageType === 'decoction') {
    return ['steep', 'finish', 'garnish']
  }
  return STAGES
}
