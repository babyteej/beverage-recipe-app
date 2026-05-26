import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Badge, ErrorMessage, Loading, Section } from '../components/ui'
import { api } from '../lib/api'
import { scaleAmount } from '../lib/utils'
import type { Recipe, RecipeIngredient } from '../types'
import { STAGE_LABELS } from '../types'

const SCALE_OPTIONS = [250, 500, 750, 1000]

export default function RecipeDetail() {
  const { id } = useParams<{ id: string }>()
  const [recipe, setRecipe] = useState<Recipe | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [unitSystem, setUnitSystem] = useState<'metric' | 'imperial'>('metric')
  const [scaleMl, setScaleMl] = useState(500)

  useEffect(() => {
    if (!id) return
    api.getRecipe(id).then(setRecipe).catch((e) => setError(e.message)).finally(() => setLoading(false))
  }, [id])

  const grouped = useMemo(() => {
    if (!recipe) return {}
    const groups: Record<string, RecipeIngredient[]> = {}
    for (const ing of recipe.ingredients) {
      const stage = ing.stage || 'other'
      groups[stage] = groups[stage] || []
      groups[stage].push(ing)
    }
    return groups
  }, [recipe])

  if (loading) return <Loading />
  if (error) return <ErrorMessage message={error} />
  if (!recipe) return null

  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="font-serif text-3xl">{recipe.name}</h1>
          {recipe.description && <p className="mt-2 text-stone-600">{recipe.description}</p>}
        </div>
        <div className="flex flex-wrap gap-2">
          {recipe.beverage_type && <Badge>{recipe.beverage_type.replace(/_/g, ' ')}</Badge>}
          {recipe.has_unverified_ingredients && <Badge variant="unverified">Unverified ingredients</Badge>}
        </div>
      </div>

      <div className="mb-8 flex flex-wrap gap-4 text-sm text-stone-600">
        <span>Yield: {scaleMl}ml {scaleMl !== 500 && `(scaled from 500ml)`}</span>
        {recipe.preparation_time_minutes != null && <span>Prep: {recipe.preparation_time_minutes} min</span>}
        {recipe.total_time_minutes != null && <span>Total: {recipe.total_time_minutes} min</span>}
      </div>

      <div className="mb-8 flex flex-wrap items-center gap-4">
        <div className="flex gap-1 rounded-lg border border-stone-200 p-1">
          {(['metric', 'imperial'] as const).map((u) => (
            <button key={u} className={`rounded px-3 py-1 text-sm capitalize ${unitSystem === u ? 'bg-sage-600 text-white' : 'text-stone-600'}`} onClick={() => setUnitSystem(u)}>
              {u}
            </button>
          ))}
        </div>
        <div>
          <label className="label inline mr-2">Scale to</label>
          <select className="input inline-block w-auto" value={scaleMl} onChange={(e) => setScaleMl(Number(e.target.value))}>
            {SCALE_OPTIONS.map((ml) => <option key={ml} value={ml}>{ml} ml</option>)}
          </select>
        </div>
        <Link to={`/recipes/${recipe.id}/edit`} className="btn-secondary">Edit</Link>
      </div>

      {recipe.equipment_required.length > 0 && (
        <Section title="Equipment">
          <ul className="flex flex-wrap gap-2">
            {recipe.equipment_required.map((e) => <Badge key={e}>{e.replace(/_/g, ' ')}</Badge>)}
          </ul>
        </Section>
      )}

      <Section title="Ingredients">
        {Object.entries(grouped).map(([stage, ings]) => (
          <div key={stage} className="mb-4">
            <h3 className="mb-2 text-sm font-medium text-stone-500">{STAGE_LABELS[stage] ?? stage.replace(/_/g, ' ')}</h3>
            <ul className="space-y-2">
              {ings.map((ing, i) => {
                const amt = unitSystem === 'metric'
                  ? scaleAmount(ing.amount_metric, recipe.yield_ml, scaleMl)
                  : scaleAmount(ing.amount_imperial, recipe.yield_ml, scaleMl)
                const unit = unitSystem === 'metric' ? ing.unit_metric : ing.unit_imperial
                return (
                  <li key={i} className="flex flex-wrap items-baseline gap-2 text-sm">
                    <span className="font-medium">{ing.ingredient_name || 'Unknown'}</span>
                    <span className="text-stone-600">{amt} {unit}</span>
                    {ing.preparation && <span className="text-stone-500">— {ing.preparation}</span>}
                    {ing.verification_status === 'unverified' && <Badge variant="unverified">Unverified</Badge>}
                  </li>
                )
              })}
            </ul>
          </div>
        ))}
      </Section>

      <Section title="Instructions">
        <ol className="list-decimal space-y-4 pl-5">
          {recipe.instructions.map((step) => (
            <li key={step.step} className="text-sm">
              <p>{step.action}</p>
              {step.equipment.length > 0 && (
                <p className="mt-1 text-stone-500">Equipment: {step.equipment.join(', ')}</p>
              )}
              {step.tip && <p className="mt-1 italic text-stone-500">Tip: {step.tip}</p>}
            </li>
          ))}
        </ol>
      </Section>

      {recipe.health_goals.length > 0 && (
        <Section title="Health goals">
          <div className="flex flex-wrap gap-1">
            {recipe.health_goals.map((g) => <Badge key={g}>{g}</Badge>)}
          </div>
        </Section>
      )}
    </div>
  )
}
