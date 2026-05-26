import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'
import { Badge, EmptyState, ErrorMessage, Loading } from '../components/ui'
import { api } from '../lib/api'
import { BEVERAGE_TYPES } from '../types'
import type { Recipe } from '../types'

export default function RecipeBrowser() {
  const [items, setItems] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({ search: '', beverage_type: '', health_goal: '' })

  useEffect(() => {
    setLoading(true)
    api.listRecipes(filters).then(setItems).catch((e) => setError(e.message)).finally(() => setLoading(false))
  }, [filters])

  return (
    <div>
      <PageHeader
        title="Recipes"
        subtitle="Saved 500ml beverage formulations — scaled display only; canonical yield stays at 500ml."
        actions={<Link to="/recipes/new" className="btn-primary">New recipe</Link>}
      />

      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        <input className="input" placeholder="Search…" value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
        <select className="input" value={filters.beverage_type} onChange={(e) => setFilters({ ...filters, beverage_type: e.target.value })}>
          <option value="">All types</option>
          {BEVERAGE_TYPES.map((b) => <option key={b} value={b}>{b.replace(/_/g, ' ')}</option>)}
        </select>
        <input className="input" placeholder="Health goal filter" value={filters.health_goal} onChange={(e) => setFilters({ ...filters, health_goal: e.target.value })} />
      </div>

      {error && <ErrorMessage message={error} />}
      {loading ? (
        <Loading />
      ) : items.length === 0 ? (
        <EmptyState
          title="No recipes yet"
          description="Generate a recipe from the combination engine, or create one manually."
          action={
            <div className="flex justify-center gap-2">
              <Link to="/combinations" className="btn-primary">Generate</Link>
              <Link to="/recipes/new" className="btn-secondary">Create manually</Link>
            </div>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {items.map((r) => (
            <Link key={r.id} to={`/recipes/${r.id}`} className="card block hover:border-sage-500">
              <div className="mb-2 flex items-start justify-between gap-2">
                <h3 className="font-serif text-lg">{r.name}</h3>
                {r.has_unverified_ingredients && <Badge variant="unverified">Data quality</Badge>}
              </div>
              {r.beverage_type && <p className="text-sm capitalize text-stone-500">{r.beverage_type.replace(/_/g, ' ')}</p>}
              {r.health_goals.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {r.health_goals.slice(0, 3).map((g) => <Badge key={g}>{g}</Badge>)}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
