import { Link } from 'react-router-dom'
import type { Ingredient } from '../types'
import { LIQUID_BASE_SUBCATEGORY } from '../types'
import { formatLabel } from '../lib/utils'
import { Badge } from './ui'

export function IngredientCard({
  ingredient,
  emphasizeHealth = false,
}: {
  ingredient: Ingredient
  emphasizeHealth?: boolean
}) {
  const unverified = ingredient.verification_status === 'unverified'
  const verified = ingredient.verification_status === 'verified'
  const isLiquidBase = ingredient.subcategory === LIQUID_BASE_SUBCATEGORY

  return (
    <Link
      to={`/ingredients/${ingredient.id}`}
      className={`group block rounded-2xl border p-5 transition-all hover:-translate-y-0.5 hover:shadow-sm ${
        unverified
          ? 'border-dashed border-amber-warn/40 bg-stone-50/90 hover:border-amber-warn/60'
          : verified
            ? 'border-stone-200 bg-white hover:border-sage-500'
            : 'border-stone-200 bg-white hover:border-sage-400'
      } ${isLiquidBase ? 'border-l-4 border-l-sky-400' : ''}`}
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <h3 className="font-serif text-lg leading-snug text-stone-900 group-hover:text-sage-700">{ingredient.name}</h3>
        <div className="flex shrink-0 flex-wrap justify-end gap-1">
          {isLiquidBase && <Badge>Liquid base</Badge>}
          {unverified && <Badge variant="unverified">Unverified</Badge>}
          {ingredient.verification_status === 'partially_verified' && (
            <Badge variant="partially_verified">Partial</Badge>
          )}
          {verified && <Badge variant="verified">Verified</Badge>}
        </div>
      </div>

      <p className="mb-3 text-xs font-medium uppercase tracking-wide text-stone-400">
        {formatLabel(ingredient.category)}
        {ingredient.primary_terpene && ` · ${ingredient.primary_terpene}`}
      </p>

      {ingredient.flavour_profile.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {ingredient.flavour_profile.slice(0, 3).map((f) => (
            <Badge key={f}>{f}</Badge>
          ))}
          {ingredient.flavour_profile.length > 3 && (
            <span className="text-xs text-stone-400">+{ingredient.flavour_profile.length - 3}</span>
          )}
        </div>
      )}

      {ingredient.body_systems.length > 0 && (
        <p className={`mt-3 truncate text-xs ${emphasizeHealth || isLiquidBase ? 'font-medium text-sage-700' : 'text-stone-500'}`}>
          {ingredient.body_systems.slice(0, 3).map(formatLabel).join(' · ')}
        </p>
      )}

      {isLiquidBase && ingredient.ratio_guidance && (
        <p className="mt-2 line-clamp-2 text-xs text-stone-500">{ingredient.ratio_guidance}</p>
      )}
    </Link>
  )
}
