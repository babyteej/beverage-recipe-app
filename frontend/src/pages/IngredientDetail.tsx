import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { BackLink } from '../components/BackLink'
import { AlertBanner, Badge, ErrorMessage, Loading, Section } from '../components/ui'
import { api } from '../lib/api'
import { formatLabel } from '../lib/utils'
import type { Ingredient } from '../types'
import { LIQUID_BASE_SUBCATEGORY } from '../types'

function ProvenancePanel({ item }: { item: Ingredient }) {
  return (
    <div className="section-card lg:sticky lg:top-24">
      <p className="label mb-3">Data provenance</p>
      <div className="flex flex-wrap gap-2">
        <Badge variant={item.entry_source_type}>{item.entry_source_type}</Badge>
        <Badge variant={item.entry_confidence}>{item.entry_confidence} confidence</Badge>
        <Badge variant={item.verification_status}>{item.verification_status}</Badge>
      </div>
      {item.last_verified_at && (
        <p className="mt-3 text-xs text-stone-500">Last verified: {new Date(item.last_verified_at).toLocaleDateString()}</p>
      )}
      {item.verification_notes && (
        <p className="mt-3 text-sm text-stone-600">{item.verification_notes}</p>
      )}
      <Link to={`/ingredients/${item.id}/edit`} className="btn-primary mt-5 w-full">
        Upgrade this entry
      </Link>
    </div>
  )
}

export default function IngredientDetail() {
  const { id } = useParams<{ id: string }>()
  const [item, setItem] = useState<Ingredient | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    api.getIngredient(id).then(setItem).catch((e) => setError(e.message)).finally(() => setLoading(false))
  }, [id])

  if (loading) return <Loading />
  if (error) return <ErrorMessage message={error} />
  if (!item) return null

  const unverified = item.verification_status === 'unverified'
  const isLiquidBase = item.subcategory === LIQUID_BASE_SUBCATEGORY

  return (
    <div>
      <BackLink to={isLiquidBase ? '/?pool=liquid_base' : '/'}>
        {isLiquidBase ? 'Liquid bases' : 'All ingredients'}
      </BackLink>

      {unverified && (
        <AlertBanner>
          This entry is AI-generated and has not been manually reviewed. Treat all claims as provisional until upgraded.
        </AlertBanner>
      )}

      <div className="mb-8">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="font-serif text-3xl tracking-tight text-stone-900">{item.name}</h1>
          {isLiquidBase && <Badge>Liquid base</Badge>}
        </div>
        {item.aliases.length > 0 && (
          <p className="mt-2 text-sm text-stone-500">{item.aliases.join(' · ')}</p>
        )}
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Section title="Identity">
            <dl className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl bg-cream-100/80 p-3"><dt className="label">Category</dt><dd className="capitalize">{item.category.replace(/_/g, ' ')}</dd></div>
              {item.subcategory && <div className="rounded-xl bg-cream-100/80 p-3"><dt className="label">Subcategory</dt><dd>{item.subcategory}</dd></div>}
              {item.origin.length > 0 && <div className="rounded-xl bg-cream-100/80 p-3 sm:col-span-2"><dt className="label">Origin</dt><dd>{item.origin.join(', ')}</dd></div>}
              {item.traditions.length > 0 && <div className="rounded-xl bg-cream-100/80 p-3 sm:col-span-2"><dt className="label">Traditions</dt><dd>{item.traditions.join(', ')}</dd></div>}
            </dl>
          </Section>

          <Section title="Flavour profile">
            <div className="flex flex-wrap gap-2">
              {item.flavour_profile.map((f) => <Badge key={f}>{f}</Badge>)}
              {item.flavour_intensity && <Badge>intensity {item.flavour_intensity}/5</Badge>}
              {item.primary_terpene && <Badge>{item.primary_terpene}</Badge>}
            </div>
          </Section>

          <Section title="Traditional claims">
            {item.health_properties.traditional_claims.length === 0 ? (
              <p className="prose-note text-stone-500">None recorded.</p>
            ) : (
              <ul className="space-y-3">
                {item.health_properties.traditional_claims.map((c, i) => (
                  <li key={i} className="rounded-xl border border-stone-200 bg-white p-4 text-sm">
                    <p className="leading-relaxed">{c.claim}</p>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      <Badge>{c.tradition}</Badge>
                      <Badge variant={c.source_type}>{c.source_type}</Badge>
                      <Badge variant={c.confidence}>{c.confidence}</Badge>
                    </div>
                    {c.source_reference && (
                      <p className="mt-2 text-xs text-stone-500">Ref: {c.source_reference}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title="Evidence-based claims">
            {item.health_properties.evidence_based_claims.length === 0 ? (
              <p className="prose-note text-stone-500">None recorded.</p>
            ) : (
              <ul className="space-y-3">
                {item.health_properties.evidence_based_claims.map((c, i) => (
                  <li key={i} className="rounded-xl border border-stone-200 bg-white p-4 text-sm">
                    <p className="leading-relaxed">{c.claim}</p>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      <Badge>{formatLabel(c.evidence_tier)}</Badge>
                      <Badge variant={c.source_type}>{c.source_type}</Badge>
                      <Badge variant={c.confidence}>{c.confidence}</Badge>
                    </div>
                    {c.source_reference && (
                      <p className="mt-2 text-xs text-stone-500">Ref: {c.source_reference}</p>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </Section>

          {(item.preparation_notes || item.bioavailability_notes || item.ratio_guidance) && (
            <Section title="Preparation">
              <div className="section-card space-y-3 prose-note">
                {item.preparation_notes && <p>{item.preparation_notes}</p>}
                {item.bioavailability_notes && <p><span className="font-medium">Bioavailability:</span> {item.bioavailability_notes}</p>}
                {item.ratio_guidance && <p><span className="font-medium">Ratio:</span> {item.ratio_guidance}</p>}
              </div>
            </Section>
          )}

          {item.contraindications.length > 0 && (
            <Section title="Contraindications">
              <ul className="section-card list-inside list-disc space-y-1 prose-note">
                {item.contraindications.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            </Section>
          )}

          {(item.history || item.sourcing_notes || item.personal_notes) && (
            <Section title="Notes">
              <div className="section-card space-y-3 prose-note">
                {item.history && <p>{item.history}</p>}
                {item.sourcing_notes && <p><span className="font-medium">Sourcing:</span> {item.sourcing_notes}</p>}
                {item.personal_notes && <p className="italic text-stone-600">{item.personal_notes}</p>}
              </div>
            </Section>
          )}
        </div>

        <div>
          <ProvenancePanel item={item} />
        </div>
      </div>
    </div>
  )
}
