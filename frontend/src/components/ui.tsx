import type { ConfidenceLevel, SourceType, VerificationStatus } from '../types'
import { formatLabel } from '../lib/utils'

const confidenceColors: Record<ConfidenceLevel, string> = {
  low: 'bg-stone-100 text-stone-600',
  medium: 'bg-amber-soft text-amber-warn',
  high: 'bg-green-100 text-green-800',
}

const verificationColors: Record<VerificationStatus, string> = {
  unverified: 'bg-amber-soft text-amber-warn border-amber-warn/30',
  partially_verified: 'bg-blue-50 text-blue-700 border-blue-200',
  verified: 'bg-green-50 text-green-800 border-green-200',
}

export function Badge({
  children,
  variant = 'default',
  className = '',
}: {
  children: React.ReactNode
  variant?: 'default' | ConfidenceLevel | VerificationStatus | SourceType
  className?: string
}) {
  let colors = 'bg-stone-100 text-stone-700'
  if (variant in confidenceColors) colors = confidenceColors[variant as ConfidenceLevel]
  if (variant in verificationColors) colors = verificationColors[variant as VerificationStatus]
  if (variant === 'ai_generated') colors = 'bg-stone-100 text-stone-600'
  if (variant === 'reference_database') colors = 'bg-blue-50 text-blue-700'
  if (variant === 'primary_text') colors = 'bg-purple-50 text-purple-700'

  return (
    <span className={`inline-flex rounded-full border border-transparent px-2.5 py-0.5 text-xs font-medium ${colors} ${className}`}>
      {typeof children === 'string' ? formatLabel(children) : children}
    </span>
  )
}

export function UnverifiedToggle({
  checked,
  onChange,
  label = 'Include unverified ingredients',
}: {
  checked: boolean
  onChange: (v: boolean) => void
  label?: string
}) {
  return (
    <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-amber-warn/30 bg-amber-soft/50 px-3 py-2 text-sm text-stone-700">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="rounded border-stone-400 text-sage-600 focus:ring-sage-500"
      />
      {label}
    </label>
  )
}

export function Loading({ message = 'Loading…' }: { message?: string }) {
  return <div className="py-16 text-center text-stone-500">{message}</div>
}

export function GeneratingProgress() {
  return (
    <div className="mb-8 rounded-xl border border-stone-200 bg-cream-100 p-8 text-center">
      <p className="mb-2 font-medium text-stone-800">Composing your recipe…</p>
      <p className="text-sm text-stone-600">
        The AI is selecting ingredients and writing full instructions.
        This usually takes 30–90 seconds — please keep this tab open.
      </p>
      <div className="mx-auto mt-4 h-1.5 w-48 overflow-hidden rounded-full bg-stone-200">
        <div className="h-full w-1/3 animate-pulse rounded-full bg-sage-600" />
      </div>
    </div>
  )
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: React.ReactNode }) {
  return (
    <div className="card-muted py-12 text-center">
      <p className="font-serif text-lg text-stone-800">{title}</p>
      <p className="mx-auto mt-2 max-w-md text-sm text-stone-600">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function AlertBanner({ variant = 'warn', children }: { variant?: 'warn' | 'info'; children: React.ReactNode }) {
  const styles = variant === 'warn'
    ? 'border-amber-warn/30 bg-amber-soft text-stone-800'
    : 'border-sage-500/20 bg-cream-100 text-stone-700'
  return (
    <div className={`mb-6 rounded-xl border px-4 py-3 text-sm leading-relaxed ${styles}`}>
      {children}
    </div>
  )
}
export function ErrorMessage({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
      {message}
    </div>
  )
}

export function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-8">
      <h2 className="mb-3 font-serif text-lg text-stone-800">{title}</h2>
      {children}
    </section>
  )
}
