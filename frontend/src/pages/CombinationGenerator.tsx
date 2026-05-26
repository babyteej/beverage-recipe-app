import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'
import { Badge, ErrorMessage, GeneratingProgress, UnverifiedToggle } from '../components/ui'
import { api } from '../lib/api'
import { setIncludeUnverified } from '../lib/utils'
import { BEVERAGE_TYPES } from '../types'
import type { Ingredient, SuggestedFormulation } from '../types'

export default function CombinationGenerator() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'anchor' | 'goal'>('anchor')
  const [ingredients, setIngredients] = useState<Ingredient[]>([])
  const [selectedAnchors, setSelectedAnchors] = useState<string[]>([])
  const [healthGoals, setHealthGoals] = useState('')
  const [beverageType, setBeverageType] = useState('')
  const [timeOfDay, setTimeOfDay] = useState('')
  const [season, setSeason] = useState('')
  const [maxIngredients, setMaxIngredients] = useState(7)
  // Default true here — all seeded ingredients are unverified; without this the picker is empty
  const [includeUnverified, setIncludeUnverifiedState] = useState(true)
  const [results, setResults] = useState<SuggestedFormulation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.listIngredients({ include_unverified: includeUnverified }).then(setIngredients).catch(() => {})
  }, [includeUnverified])

  const toggleAnchor = (id: string) => {
    setSelectedAnchors((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  const generate = async () => {
    if (mode === 'anchor' && selectedAnchors.length === 0) {
      setError('Select at least one anchor ingredient.')
      return
    }
    if (mode === 'goal' && !healthGoals.trim()) {
      setError('Enter at least one health goal.')
      return
    }
    if (!includeUnverified && ingredients.length === 0) {
      setError('No verified ingredients available. Enable "Include unverified ingredients" or verify some entries first.')
      return
    }

    setLoading(true)
    setError('')
    setResults([])
    try {
      const res = await api.suggestCombinations({
        mode,
        anchor_ingredient_ids: mode === 'anchor' ? selectedAnchors : undefined,
        health_goals: mode === 'goal' ? healthGoals.split(',').map((s) => s.trim()).filter(Boolean) : undefined,
        include_unverified: includeUnverified,
        constraints: {
          beverage_type: beverageType || undefined,
          time_of_day: timeOfDay || undefined,
          season: season || undefined,
          max_ingredients: maxIngredients,
        },
      })
      setResults(res.formulations)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  const saveFormulation = async (f: SuggestedFormulation) => {
    try {
      const recipe = await api.createRecipe({
        ...f,
        yield_ml: 500,
      })
      navigate(`/recipes/${recipe.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed')
    }
  }

  return (
    <div>
      <PageHeader
        title="Combination generator"
        subtitle="Build complete 500ml recipes from your ingredient database — anchor mode features specific ingredients, goal mode targets health outcomes."
      />

      <div className="mb-6 flex gap-2">
        {(['anchor', 'goal'] as const).map((m) => (
          <button
            key={m}
            className={mode === m ? 'btn-primary' : 'btn-secondary'}
            onClick={() => setMode(m)}
            disabled={loading}
          >
            {m === 'anchor' ? 'Anchor mode' : 'Goal mode'}
          </button>
        ))}
      </div>

      <div className="mb-6">
        <UnverifiedToggle
          checked={includeUnverified}
          onChange={(v) => { setIncludeUnverified(v); setIncludeUnverifiedState(v) }}
        />
        {!includeUnverified && ingredients.length === 0 && (
          <p className="mt-2 text-sm text-amber-warn">
            No verified ingredients yet — turn on unverified to use your seeded database.
          </p>
        )}
      </div>

      {mode === 'anchor' ? (
        <div className="mb-6">
          <label className="label">Select anchor ingredient(s)</label>
          {ingredients.length === 0 ? (
            <p className="text-sm text-stone-500">No ingredients available. Enable unverified ingredients above.</p>
          ) : (
            <div className="max-h-48 overflow-y-auto rounded-lg border border-stone-200 bg-white p-2">
              {ingredients.map((i) => (
                <label key={i.id} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-cream-100">
                  <input type="checkbox" checked={selectedAnchors.includes(i.id)} onChange={() => toggleAnchor(i.id)} disabled={loading} />
                  <span className="text-sm">{i.name}</span>
                  {i.verification_status === 'unverified' && <Badge variant="unverified">Unverified</Badge>}
                </label>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="mb-6">
          <label className="label">Health goals (comma-separated)</label>
          <input
            className="input"
            placeholder="e.g. gut health and regularity, high fiber, nervous system support"
            value={healthGoals}
            onChange={(e) => setHealthGoals(e.target.value)}
            disabled={loading}
          />
        </div>
      )}

      <div className="mb-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label className="label">Beverage type</label>
          <select className="input" value={beverageType} onChange={(e) => setBeverageType(e.target.value)} disabled={loading}>
            <option value="">Any</option>
            {BEVERAGE_TYPES.map((b) => <option key={b} value={b}>{b.replace(/_/g, ' ')}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Time of day</label>
          <select className="input" value={timeOfDay} onChange={(e) => setTimeOfDay(e.target.value)} disabled={loading}>
            <option value="">Any</option>
            {['morning', 'afternoon', 'evening', 'night'].map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Season</label>
          <select className="input" value={season} onChange={(e) => setSeason(e.target.value)} disabled={loading}>
            <option value="">Any</option>
            {['spring', 'summer', 'fall', 'winter'].map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="label">Max ingredients</label>
          <input className="input" type="number" min={3} max={12} value={maxIngredients} onChange={(e) => setMaxIngredients(Number(e.target.value))} disabled={loading} />
        </div>
      </div>

      <button className="btn-primary mb-8" onClick={generate} disabled={loading}>
        {loading ? 'Generating… (30–90 sec)' : 'Generate recipe'}
      </button>

      {error && <div className="mb-6"><ErrorMessage message={error} /></div>}

      {loading && <GeneratingProgress />}

      <div className="space-y-6">
        {results.map((f, idx) => (
          <div key={idx} className="card">
            <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="font-serif text-xl">{f.name}</h2>
                <p className="text-sm text-stone-600">{f.description}</p>
              </div>
              <div className="flex gap-2">
                {f.contains_unverified_ingredients && <Badge variant="unverified">Unverified data</Badge>}
                <Badge>{f.beverage_type.replace(/_/g, ' ')}</Badge>
              </div>
            </div>

            <p className="mb-4 text-sm italic text-stone-600">{f.reasoning}</p>

            <h3 className="label mb-2">Ingredients</h3>
            <ul className="mb-4 space-y-1 text-sm">
              {f.ingredients.map((ing, i) => {
                const name = ingredients.find((x) => x.id === ing.ingredient_id)?.name || ing.ingredient_id
                return (
                  <li key={i}>
                    {name}: {ing.amount_metric}{ing.unit_metric} / {ing.amount_imperial}{ing.unit_imperial} ({ing.stage})
                  </li>
                )
              })}
            </ul>

            <h3 className="label mb-2">Instructions</h3>
            <ol className="mb-4 list-decimal space-y-2 pl-5 text-sm">
              {f.instructions.map((step) => (
                <li key={step.step}>{step.action}</li>
              ))}
            </ol>

            <div className="flex gap-2">
              <button className="btn-primary" onClick={() => saveFormulation(f)}>Save this recipe</button>
              <button className="btn-secondary" onClick={generate} disabled={loading}>Generate another</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
