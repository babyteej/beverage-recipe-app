import { Link } from 'react-router-dom'
import type { ReactNode } from 'react'

export function BackLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link to={to} className="mb-6 inline-flex items-center gap-1 text-sm text-sage-600 hover:text-sage-700">
      ← {children}
    </Link>
  )
}
