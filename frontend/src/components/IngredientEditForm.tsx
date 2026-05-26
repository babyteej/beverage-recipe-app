import { useState } from 'react'
import type {
  ConfidenceLevel,
  EvidenceBasedClaim,
  Ingredient,
  SourceType,
  TraditionalClaim,
  VerificationStatus,
} from '../types'
import { CATEGORIES, TERPENES } from '../types'
import { joinList, splitList } from '../lib/utils'
import { Field, FieldGrid, FormSection } from './FormSection'
import { Badge } from './ui'

const SOURCE_TYPES: SourceType[] = [
  'ai_generated', 'reference_database', 'primary_text', 'personal_research', 'practitioner_knowledge',
]
const CONFIDENCE: ConfidenceLevel[] = ['low', 'medium', 'high']
const EVIDENCE_TIERS = ['traditional_consensus', 'preliminary_research', 'established_research', 'conflicting_evidence']

type FormState = Omit<Ingredient, 'id' | 'created_at' | 'updated_at'>

function toFormState(item: Ingredient): FormState {
  const { id, created_at, updated_at, ...rest } = item
  // API may include read-only fields not accepted on PUT (e.g. deleted_at)
  const { deleted_at: _deletedAt, ...editable } = rest as FormState & { deleted_at?: string | null }
  return editable
}

export function IngredientEditForm({
  initial,
  onSave,
  saving,
}: {
  initial: Ingredient
  onSave: (data: FormState) => Promise<void>
  saving: boolean
}) {
  const [form, setForm] = useState<FormState>(() => toFormState(initial))
  const [showAdvanced, setShowAdvanced] = useState(false)

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const updateTraditional = (index: number, patch: Partial<TraditionalClaim>) => {
    const claims = [...form.health_properties.traditional_claims]
    claims[index] = { ...claims[index], ...patch }
    set('health_properties', { ...form.health_properties, traditional_claims: claims })
  }

  const updateEvidence = (index: number, patch: Partial<EvidenceBasedClaim>) => {
    const claims = [...form.health_properties.evidence_based_claims]
    claims[index] = { ...claims[index], ...patch }
    set('health_properties', { ...form.health_properties, evidence_based_claims: claims })
  }

  const addTraditional = () => {
    set('health_properties', {
      ...form.health_properties,
      traditional_claims: [
        ...form.health_properties.traditional_claims,
        { claim: '', tradition: '', source_type: 'reference_database', source_reference: null, confidence: 'medium' },
      ],
    })
  }

  const addEvidence = () => {
    set('health_properties', {
      ...form.health_properties,
      evidence_based_claims: [
        ...form.health_properties.evidence_based_claims,
        { claim: '', evidence_tier: 'preliminary_research', source_type: 'reference_database', source_reference: null, confidence: 'medium' },
      ],
    })
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onSave(form)
      }}
      className="space-y-2"
    >
      <FormSection title="Provenance & verification" description="Update trust level and document what you checked.">
        <FieldGrid>
          <Field label="Verification status">
            <select className="input" value={form.verification_status} onChange={(e) => set('verification_status', e.target.value as VerificationStatus)}>
              <option value="unverified">Unverified</option>
              <option value="partially_verified">Partially verified</option>
              <option value="verified">Verified</option>
            </select>
          </Field>
          <Field label="Entry source type">
            <select className="input" value={form.entry_source_type} onChange={(e) => set('entry_source_type', e.target.value as SourceType)}>
              {SOURCE_TYPES.map((s) => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
            </select>
          </Field>
          <Field label="Entry confidence">
            <select className="input" value={form.entry_confidence} onChange={(e) => set('entry_confidence', e.target.value as ConfidenceLevel)}>
              {CONFIDENCE.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Verification notes" className="sm:col-span-2">
            <textarea
              className="input min-h-[80px]"
              value={form.verification_notes || ''}
              onChange={(e) => set('verification_notes', e.target.value || null)}
              placeholder="What was checked, against which source (e.g. MSKCC About Herbs, Charaka Samhita 1.4.27)"
            />
          </Field>
        </FieldGrid>
      </FormSection>

      <FormSection title="Identity">
        <FieldGrid>
          <Field label="Name" className="sm:col-span-2">
            <input className="input font-serif text-base" value={form.name} onChange={(e) => set('name', e.target.value)} required />
          </Field>
          <Field label="Category">
            <select className="input" value={form.category} onChange={(e) => set('category', e.target.value)}>
              {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>)}
            </select>
          </Field>
          <Field label="Subcategory">
            <input className="input" value={form.subcategory || ''} onChange={(e) => set('subcategory', e.target.value || null)} />
          </Field>
          <Field label="Aliases (comma-separated)" className="sm:col-span-2">
            <input className="input" value={joinList(form.aliases)} onChange={(e) => set('aliases', splitList(e.target.value))} />
          </Field>
          <Field label="Origin regions">
            <input className="input" value={joinList(form.origin)} onChange={(e) => set('origin', splitList(e.target.value))} />
          </Field>
          <Field label="Traditions">
            <input className="input" value={joinList(form.traditions)} onChange={(e) => set('traditions', splitList(e.target.value))} />
          </Field>
        </FieldGrid>
      </FormSection>

      <FormSection title="Flavour & chemistry">
        <FieldGrid>
          <Field label="Flavour profile">
            <input className="input" value={joinList(form.flavour_profile)} onChange={(e) => set('flavour_profile', splitList(e.target.value))} placeholder="bitter, earthy, floral" />
          </Field>
          <Field label="Flavour intensity (1–5)">
            <input className="input" type="number" min={1} max={5} value={form.flavour_intensity ?? ''} onChange={(e) => set('flavour_intensity', e.target.value ? Number(e.target.value) : null)} />
          </Field>
          <Field label="Primary terpene">
            <select className="input" value={form.primary_terpene || ''} onChange={(e) => set('primary_terpene', e.target.value || null)}>
              <option value="">—</option>
              {TERPENES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
          </Field>
          <Field label="Beverage types">
            <input className="input" value={joinList(form.beverage_types)} onChange={(e) => set('beverage_types', splitList(e.target.value))} placeholder="smoothie, cold_press_juice, hot_tea" />
          </Field>
          <Field label="Body systems" className="sm:col-span-2">
            <input className="input" value={joinList(form.body_systems)} onChange={(e) => set('body_systems', splitList(e.target.value))} placeholder="gut, immune, nervous_system" />
          </Field>
        </FieldGrid>
      </FormSection>

      <FormSection title="Traditional claims">
        <div className="space-y-4">
          {form.health_properties.traditional_claims.map((claim, i) => (
            <div key={i} className="rounded-xl border border-stone-200 bg-cream-50/50 p-4">
              <Field label="Claim">
                <textarea className="input min-h-[60px]" value={claim.claim} onChange={(e) => updateTraditional(i, { claim: e.target.value })} />
              </Field>
              <FieldGrid>
                <Field label="Tradition">
                  <input className="input" value={claim.tradition} onChange={(e) => updateTraditional(i, { tradition: e.target.value })} />
                </Field>
                <Field label="Source type">
                  <select className="input" value={claim.source_type} onChange={(e) => updateTraditional(i, { source_type: e.target.value as SourceType })}>
                    {SOURCE_TYPES.map((s) => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
                  </select>
                </Field>
                <Field label="Source reference">
                  <input className="input" value={claim.source_reference || ''} onChange={(e) => updateTraditional(i, { source_reference: e.target.value || null })} />
                </Field>
                <Field label="Confidence">
                  <select className="input" value={claim.confidence} onChange={(e) => updateTraditional(i, { confidence: e.target.value as ConfidenceLevel })}>
                    {CONFIDENCE.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </Field>
              </FieldGrid>
              <button type="button" className="btn-ghost mt-2 text-xs text-red-600" onClick={() => {
                set('health_properties', {
                  ...form.health_properties,
                  traditional_claims: form.health_properties.traditional_claims.filter((_, idx) => idx !== i),
                })
              }}>Remove claim</button>
            </div>
          ))}
          <button type="button" className="btn-secondary" onClick={addTraditional}>+ Add traditional claim</button>
        </div>
      </FormSection>

      <FormSection title="Evidence-based claims">
        <div className="space-y-4">
          {form.health_properties.evidence_based_claims.map((claim, i) => (
            <div key={i} className="rounded-xl border border-stone-200 bg-cream-50/50 p-4">
              <Field label="Claim">
                <textarea className="input min-h-[60px]" value={claim.claim} onChange={(e) => updateEvidence(i, { claim: e.target.value })} />
              </Field>
              <FieldGrid>
                <Field label="Evidence tier">
                  <select className="input" value={claim.evidence_tier} onChange={(e) => updateEvidence(i, { evidence_tier: e.target.value as EvidenceBasedClaim['evidence_tier'] })}>
                    {EVIDENCE_TIERS.map((t) => <option key={t} value={t}>{t.replace(/_/g, ' ')}</option>)}
                  </select>
                </Field>
                <Field label="Source type">
                  <select className="input" value={claim.source_type} onChange={(e) => updateEvidence(i, { source_type: e.target.value as SourceType })}>
                    {SOURCE_TYPES.map((s) => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
                  </select>
                </Field>
                <Field label="Source reference">
                  <input className="input" value={claim.source_reference || ''} onChange={(e) => updateEvidence(i, { source_reference: e.target.value || null })} />
                </Field>
                <Field label="Confidence">
                  <select className="input" value={claim.confidence} onChange={(e) => updateEvidence(i, { confidence: e.target.value as ConfidenceLevel })}>
                    {CONFIDENCE.map((c) => <option key={c} value={c}>{c}</option>)}
                  </select>
                </Field>
              </FieldGrid>
              <button type="button" className="btn-ghost mt-2 text-xs text-red-600" onClick={() => {
                set('health_properties', {
                  ...form.health_properties,
                  evidence_based_claims: form.health_properties.evidence_based_claims.filter((_, idx) => idx !== i),
                })
              }}>Remove claim</button>
            </div>
          ))}
          <button type="button" className="btn-secondary" onClick={addEvidence}>+ Add evidence claim</button>
        </div>
      </FormSection>

      <FormSection title="Preparation & safety">
        <FieldGrid>
          <Field label="Preparation notes" className="sm:col-span-2">
            <textarea className="input min-h-[80px]" value={form.preparation_notes || ''} onChange={(e) => set('preparation_notes', e.target.value || null)} />
          </Field>
          <Field label="Bioavailability notes" className="sm:col-span-2">
            <textarea className="input min-h-[60px]" value={form.bioavailability_notes || ''} onChange={(e) => set('bioavailability_notes', e.target.value || null)} />
          </Field>
          <Field label="Ratio guidance" className="sm:col-span-2">
            <textarea className="input min-h-[60px]" value={form.ratio_guidance || ''} onChange={(e) => set('ratio_guidance', e.target.value || null)} />
          </Field>
          <Field label="Contraindications" className="sm:col-span-2">
            <textarea className="input min-h-[60px]" value={joinList(form.contraindications)} onChange={(e) => set('contraindications', splitList(e.target.value))} placeholder="One per comma-separated entry" />
          </Field>
        </FieldGrid>
      </FormSection>

      <FormSection title="Notes">
        <FieldGrid>
          <Field label="History" className="sm:col-span-2">
            <textarea className="input min-h-[80px]" value={form.history || ''} onChange={(e) => set('history', e.target.value || null)} />
          </Field>
          <Field label="Sourcing notes" className="sm:col-span-2">
            <textarea className="input min-h-[60px]" value={form.sourcing_notes || ''} onChange={(e) => set('sourcing_notes', e.target.value || null)} />
          </Field>
          <Field label="Personal notes" className="sm:col-span-2">
            <textarea className="input min-h-[60px]" value={form.personal_notes || ''} onChange={(e) => set('personal_notes', e.target.value || null)} />
          </Field>
        </FieldGrid>
      </FormSection>

      <div className="mt-6">
        <button type="button" className="btn-ghost text-sm" onClick={() => setShowAdvanced(!showAdvanced)}>
          {showAdvanced ? 'Hide' : 'Show'} advanced JSON
        </button>
        {showAdvanced && (
          <pre className="mt-3 max-h-64 overflow-auto rounded-xl border border-stone-200 bg-stone-50 p-4 text-xs">{JSON.stringify(form, null, 2)}</pre>
        )}
      </div>

      <div className="sticky bottom-0 -mx-4 mt-8 flex items-center justify-between gap-4 border-t border-stone-200 bg-cream-50/95 px-4 py-4 backdrop-blur-sm sm:-mx-0 sm:rounded-2xl sm:border sm:px-6">
        <div className="flex flex-wrap gap-2">
          <Badge variant={form.verification_status}>{form.verification_status}</Badge>
          <Badge variant={form.entry_source_type}>{form.entry_source_type}</Badge>
        </div>
        <button type="submit" className="btn-primary" disabled={saving}>
          {saving ? 'Saving…' : 'Save upgrade'}
        </button>
      </div>
    </form>
  )
}
