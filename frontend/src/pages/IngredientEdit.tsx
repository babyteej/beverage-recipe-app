import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { BackLink } from '../components/BackLink'
import { IngredientEditForm } from '../components/IngredientEditForm'
import { PageHeader } from '../components/PageHeader'
import { ErrorMessage, Loading } from '../components/ui'
import { api } from '../lib/api'
import type { Ingredient } from '../types'

export default function IngredientEdit() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [item, setItem] = useState<Ingredient | null>(null)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!id) return
    api.getIngredient(id).then(setItem).catch((e) => setError(e.message))
  }, [id])

  const save = async (data: Omit<Ingredient, 'id' | 'created_at' | 'updated_at'>) => {
    if (!id) return
    setSaving(true)
    setError('')
    try {
      await api.updateIngredient(id, data)
      navigate(`/ingredients/${id}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  if (!item && !error) return <Loading />
  if (error && !item) return <ErrorMessage message={error} />

  return (
    <div>
      <BackLink to={`/ingredients/${id}`}>Back to ingredient</BackLink>
      <PageHeader
        title="Upgrade entry"
        subtitle="Review and improve this ingredient. Change source types per claim, add citations, and update verification status."
      />
      {error && <div className="mb-6"><ErrorMessage message={error} /></div>}
      {item && <IngredientEditForm initial={item} onSave={save} saving={saving} />}
    </div>
  )
}
