import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { IngredientCard } from '../components/IngredientCard'
import { PageHeader } from '../components/PageHeader'
import { EmptyState, ErrorMessage, Loading, UnverifiedToggle } from '../components/ui'
import { api } from '../lib/api'
import { getIncludeUnverified, setIncludeUnverified } from '../lib/utils'
import {
  BEVERAGE_TYPES,
  BODY_SYSTEMS,
  CATEGORIES,
  INGREDIENT_POOLS,
  LIQUID_BASE_SUBCATEGORY,
  TERPENES,
  type IngredientPoolFilter,
} from '../types'
import type { Ingredient } from '../types'

function poolToApiParams(pool: IngredientPoolFilter) {
  if (pool === 'liquid_base') return { subcategory: LIQUID_BASE_SUBCATEGORY }
  if (pool === 'blend') return { exclude_subcategory: LIQUID_BASE_SUBCATEGORY }
  return {}
}

export default function IngredientBrowser() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialPool = (searchParams.get('pool') || '') as IngredientPoolFilter
  const poolFromUrl = INGREDIENT_POOLS.some((p) => p.value === initialPool) ? initialPool : ''

  const [items, setItems] = useState<Ingredient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [includeUnverified, setIncludeUnverifiedState] = useState(getIncludeUnverified())
  const [filters, setFilters] = useState({
    search: '',
    pool: poolFromUrl,
    category: '',
    terpene: '',
    body_system: '',
    beverage_type: '',
    verification_status: '',
  })

  useEffect(() => {
    const urlPool = (searchParams.get('pool') || '') as IngredientPoolFilter
    const validPool = INGREDIENT_POOLS.some((p) => p.value === urlPool) ? urlPool : ''
    setFilters((prev) => (prev.pool === validPool ? prev : { ...prev, pool: validPool }))
  }, [searchParams])

  const apiParams = useMemo(() => {
    const { pool, ...rest } = filters
    return {
      ...rest,
      ...poolToApiParams(pool),
      include_unverified: includeUnverified,
    }
  }, [filters, includeUnverified])

  useEffect(() => {
    setLoading(true)
    setError('')
    api
      .listIngredients(apiParams)
      .then(setItems)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [apiParams])

  const handleUnverifiedToggle = (v: boolean) => {
    setIncludeUnverified(v)
    setIncludeUnverifiedState(v)
  }

  const setPool = (pool: IngredientPoolFilter) => {
    setFilters({ ...filters, pool })
    const next = new URLSearchParams(searchParams)
    if (pool) next.set('pool', pool)
    else next.delete('pool')
    setSearchParams(next, { replace: true })
  }

  const verifiedCount = items.filter((i) => i.verification_status !== 'unverified').length
  const unverifiedCount = items.filter((i) => i.verification_status === 'unverified').length
  const poolLabel = INGREDIENT_POOLS.find((p) => p.value === filters.pool)?.label ?? 'All ingredients'

  const emptyDescription = (() => {
    if (!includeUnverified) {
      return 'All seeded entries are still unverified. Toggle "Include unverified ingredients" above to browse them, or verify entries from the Verify queue.'
    }
    if (filters.pool === 'liquid_base') {
      return 'No liquid bases match your filters. Try clearing category or beverage type filters.'
    }
    if (filters.pool === 'blend') {
      return 'No blend ingredients match your filters. Try adjusting search or filters.'
    }
    return 'Try adjusting your filters or search term.'
  })()

  return (
    <div>
      <PageHeader
        title="Ingredients"
        subtitle="Your curated knowledge base. Verified entries show by default; unverified AI-seeded data is always labeled."
        actions={<UnverifiedToggle checked={includeUnverified} onChange={handleUnverifiedToggle} />}
      />

      <div className="filter-panel">
        <p className="label mb-3">Pool</p>
        <div className="mb-4 flex flex-wrap gap-2">
          {INGREDIENT_POOLS.map((pool) => (
            <button
              key={pool.value || 'all'}
              type="button"
              className={
                filters.pool === pool.value
                  ? 'btn-primary text-sm'
                  : 'btn-secondary text-sm'
              }
              onClick={() => setPool(pool.value)}
            >
              {pool.label}
            </button>
          ))}
        </div>

        <p className="label mb-3">Filters</p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <input
            className="input sm:col-span-2 lg:col-span-3"
            placeholder="Search by name…"
            value={filters.search}
            onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          />
          <select className="input" value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
            <option value="">All categories</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>
            ))}
          </select>
          <select className="input" value={filters.terpene} onChange={(e) => setFilters({ ...filters, terpene: e.target.value })}>
            <option value="">All terpenes</option>
            {TERPENES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <select className="input" value={filters.body_system} onChange={(e) => setFilters({ ...filters, body_system: e.target.value })}>
            <option value="">All body systems</option>
            {BODY_SYSTEMS.map((b) => (
              <option key={b} value={b}>{b.replace(/_/g, ' ')}</option>
            ))}
          </select>
          <select className="input" value={filters.beverage_type} onChange={(e) => setFilters({ ...filters, beverage_type: e.target.value })}>
            <option value="">All beverage types</option>
            {BEVERAGE_TYPES.map((b) => (
              <option key={b} value={b}>{b.replace(/_/g, ' ')}</option>
            ))}
          </select>
          {includeUnverified && (
            <select className="input" value={filters.verification_status} onChange={(e) => setFilters({ ...filters, verification_status: e.target.value })}>
              <option value="">All verification statuses</option>
              <option value="unverified">Unverified</option>
              <option value="partially_verified">Partially verified</option>
              <option value="verified">Verified</option>
            </select>
          )}
        </div>
      </div>

      {!loading && items.length > 0 && (
        <p className="mb-4 text-sm text-stone-500">
          Showing {items.length} {poolLabel.toLowerCase()}
          {includeUnverified && ` · ${verifiedCount} verified/partial · ${unverifiedCount} unverified`}
        </p>
      )}

      {error && <ErrorMessage message={error} />}
      {loading ? (
        <Loading />
      ) : items.length === 0 ? (
        <EmptyState title="No ingredients found" description={emptyDescription} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((i) => (
            <IngredientCard key={i.id} ingredient={i} emphasizeHealth={filters.pool === 'liquid_base'} />
          ))}
        </div>
      )}
    </div>
  )
}
