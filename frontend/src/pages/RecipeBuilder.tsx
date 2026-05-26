import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ErrorMessage, UnverifiedToggle } from '../components/ui'
import { api } from '../lib/api'
import { getIncludeUnverified, setIncludeUnverified } from '../lib/utils'
import { BEVERAGE_TYPES, STAGE_LABELS, stagesForBeverageType } from '../types'
import type { Ingredient, RecipeIngredient, RecipeInstruction } from '../types'

const emptyIngredient = (): RecipeIngredient => ({
  ingredient_id: '',
  amount_metric: 0,
  unit_metric: 'g',
  amount_imperial: 0,
  unit_imperial: 'oz',
  preparation: '',
  stage: 'press',
  notes: '',
})

const emptyStep = (step: number): RecipeInstruction => ({
  step,
  action: '',
  duration_seconds: null,
  equipment: [],
  tip: null,
})

export default function RecipeBuilder() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isEdit = Boolean(id)

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [beverageType, setBeverageType] = useState('')
  const [prepTime, setPrepTime] = useState<number | ''>('')
  const [totalTime, setTotalTime] = useState<number | ''>('')
  const [healthGoals, setHealthGoals] = useState('')
  const [ingredients, setIngredients] = useState<RecipeIngredient[]>([emptyIngredient()])
  const [instructions, setInstructions] = useState<RecipeInstruction[]>([emptyStep(1)])
  const [pickerItems, setPickerItems] = useState<Ingredient[]>([])
  const [includeUnverified, setIncludeUnverifiedState] = useState(getIncludeUnverified())
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.listIngredients({ include_unverified: includeUnverified }).then(setPickerItems).catch(() => {})
  }, [includeUnverified])

  useEffect(() => {
    if (!id) return
    api.getRecipe(id).then((r) => {
      setName(r.name)
      setDescription(r.description || '')
      setBeverageType(r.beverage_type || '')
      setPrepTime(r.preparation_time_minutes ?? '')
      setTotalTime(r.total_time_minutes ?? '')
      setHealthGoals(r.health_goals.join(', '))
      setIngredients(r.ingredients)
      setInstructions(r.instructions)
    }).catch((e) => setError(e.message))
  }, [id])

  const updateIngredient = (idx: number, field: keyof RecipeIngredient, value: string | number) => {
    setIngredients((prev) => prev.map((ing, i) => (i === idx ? { ...ing, [field]: value } : ing)))
  }

  const updateInstruction = (idx: number, field: keyof RecipeInstruction, value: string | number | string[] | null) => {
    setInstructions((prev) => prev.map((s, i) => (i === idx ? { ...s, [field]: value } : s)))
  }

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      const payload = {
        name,
        description: description || null,
        beverage_type: beverageType || null,
        yield_ml: 500,
        preparation_time_minutes: prepTime === '' ? null : Number(prepTime),
        total_time_minutes: totalTime === '' ? null : Number(totalTime),
        health_goals: healthGoals.split(',').map((s) => s.trim()).filter(Boolean),
        ingredients,
        instructions,
        equipment_required: [...new Set(instructions.flatMap((s) => s.equipment))],
        body_systems_targeted: [],
        tags: [],
        contraindications: [],
        terpene_profile: [],
        sensory_profile: {},
        contextual_fit: {},
      }
      const recipe = isEdit && id
        ? await api.updateRecipe(id, payload)
        : await api.createRecipe(payload)
      navigate(`/recipes/${recipe.id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  const hasUnverified = ingredients.some((ing) => {
    const meta = pickerItems.find((p) => p.id === ing.ingredient_id)
    return meta?.verification_status === 'unverified'
  })

  return (
    <div>
      <h1 className="mb-6 font-serif text-3xl">{isEdit ? 'Edit recipe' : 'New recipe'}</h1>

      {hasUnverified && (
        <div className="mb-6 rounded-lg border border-amber-warn/40 bg-amber-soft px-4 py-3 text-sm">
          This recipe includes unverified ingredients — data quality warning applies until verified.
        </div>
      )}

      <div className="mb-4">
        <UnverifiedToggle checked={includeUnverified} onChange={(v) => { setIncludeUnverified(v); setIncludeUnverifiedState(v) }} label="Include unverified ingredients in picker" />
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2">
        <div><label className="label">Name</label><input className="input" value={name} onChange={(e) => setName(e.target.value)} /></div>
        <div>
          <label className="label">Beverage type</label>
          <select className="input" value={beverageType} onChange={(e) => setBeverageType(e.target.value)}>
            <option value="">Select…</option>
            {BEVERAGE_TYPES.map((b) => <option key={b} value={b}>{b.replace(/_/g, ' ')}</option>)}
          </select>
        </div>
        <div className="sm:col-span-2"><label className="label">Description</label><textarea className="input" value={description} onChange={(e) => setDescription(e.target.value)} /></div>
        <div><label className="label">Prep time (min)</label><input className="input" type="number" value={prepTime} onChange={(e) => setPrepTime(e.target.value === '' ? '' : Number(e.target.value))} /></div>
        <div><label className="label">Total time (min)</label><input className="input" type="number" value={totalTime} onChange={(e) => setTotalTime(e.target.value === '' ? '' : Number(e.target.value))} /></div>
        <div className="sm:col-span-2"><label className="label">Health goals (comma-separated)</label><input className="input" value={healthGoals} onChange={(e) => setHealthGoals(e.target.value)} /></div>
      </div>

      <h2 className="mb-3 font-serif text-lg">Ingredients <span className="text-sm font-sans text-stone-500">(yield: 500ml)</span></h2>
      {beverageType === 'smoothie' && (
        <p className="mb-3 text-sm text-stone-600">
          Smoothies need a <strong>liquid base</strong> (100–150ml water, coconut water, or nut milk) plus{' '}
          <strong>blend</strong> ingredients (produce, seeds). Use a blender — not a juicer.
        </p>
      )}
      <div className="mb-6 space-y-3">
        {ingredients.map((ing, idx) => (
          <div key={idx} className="grid gap-2 rounded-lg border border-stone-200 p-3 sm:grid-cols-6">
            <select className="input sm:col-span-2" value={ing.ingredient_id} onChange={(e) => updateIngredient(idx, 'ingredient_id', e.target.value)}>
              <option value="">Select ingredient…</option>
              {pickerItems.map((p) => (
                <option key={p.id} value={p.id}>{p.name}{p.verification_status === 'unverified' ? ' (unverified)' : ''}</option>
              ))}
            </select>
            <input className="input" placeholder="Metric amt" type="number" value={ing.amount_metric || ''} onChange={(e) => updateIngredient(idx, 'amount_metric', Number(e.target.value))} />
            <input className="input" placeholder="Unit" value={ing.unit_metric} onChange={(e) => updateIngredient(idx, 'unit_metric', e.target.value)} />
            <input className="input" placeholder="Imperial amt" type="number" value={ing.amount_imperial || ''} onChange={(e) => updateIngredient(idx, 'amount_imperial', Number(e.target.value))} />
            <select className="input" value={ing.stage} onChange={(e) => updateIngredient(idx, 'stage', e.target.value)}>
              {stagesForBeverageType(beverageType).map((s) => (
                <option key={s} value={s}>{STAGE_LABELS[s] ?? s}</option>
              ))}
            </select>
          </div>
        ))}
        <button className="btn-secondary" type="button" onClick={() => setIngredients([...ingredients, emptyIngredient()])}>+ Add ingredient</button>
      </div>

      <h2 className="mb-3 font-serif text-lg">Instructions</h2>
      <div className="mb-6 space-y-3">
        {instructions.map((step, idx) => (
          <div key={idx} className="rounded-lg border border-stone-200 p-3">
            <label className="label">Step {step.step}</label>
            <textarea className="input mb-2" value={step.action} onChange={(e) => updateInstruction(idx, 'action', e.target.value)} />
            <input className="input" placeholder="Equipment (comma-separated)" value={step.equipment.join(', ')} onChange={(e) => updateInstruction(idx, 'equipment', e.target.value.split(',').map((s) => s.trim()).filter(Boolean))} />
          </div>
        ))}
        <button className="btn-secondary" type="button" onClick={() => setInstructions([...instructions, emptyStep(instructions.length + 1)])}>+ Add step</button>
      </div>

      {error && <div className="mb-4"><ErrorMessage message={error} /></div>}

      <div className="flex gap-2">
        <button className="btn-primary" onClick={save} disabled={saving}>{saving ? 'Saving…' : 'Save recipe'}</button>
        <Link to="/recipes" className="btn-secondary">Cancel</Link>
      </div>
    </div>
  )
}
