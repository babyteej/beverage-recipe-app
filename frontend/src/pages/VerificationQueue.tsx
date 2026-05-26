import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'
import { Badge, EmptyState, ErrorMessage, Loading } from '../components/ui'
import { api } from '../lib/api'
import { formatLabel } from '../lib/utils'
import type { VerificationQueueItem } from '../types'

export default function VerificationQueue() {
  const [items, setItems] = useState<VerificationQueueItem[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.verificationQueue().then(setItems).catch((e) => setError(e.message)).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <PageHeader
        title="Verification queue"
        subtitle="Unverified entries sorted by how often they appear in your saved recipes — verify what you actually use."
      />

      {error && <ErrorMessage message={error} />}
      {loading ? (
        <Loading />
      ) : items.length === 0 ? (
        <EmptyState title="Queue is empty" description="All entries are verified, or you haven't seeded any unverified ingredients yet." />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-stone-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-stone-200 bg-cream-100/80">
              <tr>
                <th className="px-5 py-3.5 font-semibold text-stone-600">Ingredient</th>
                <th className="px-5 py-3.5 font-semibold text-stone-600">Category</th>
                <th className="px-5 py-3.5 font-semibold text-stone-600">Confidence</th>
                <th className="px-5 py-3.5 font-semibold text-stone-600">In recipes</th>
                <th className="px-5 py-3.5"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-b border-stone-100 last:border-0 hover:bg-cream-50/50">
                  <td className="px-5 py-4 font-serif text-stone-900">{item.name}</td>
                  <td className="px-5 py-4 capitalize text-stone-600">{formatLabel(item.category)}</td>
                  <td className="px-5 py-4"><Badge variant={item.entry_confidence}>{item.entry_confidence}</Badge></td>
                  <td className="px-5 py-4 tabular-nums text-stone-600">{item.usage_count}</td>
                  <td className="px-5 py-4 text-right">
                    <Link to={`/ingredients/${item.id}/edit`} className="btn-secondary text-xs">
                      Verify now
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
