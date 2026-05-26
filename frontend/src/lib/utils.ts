export function formatLabel(value: string): string {
  return value.replace(/_/g, ' ')
}

export function getIncludeUnverified(): boolean {
  return localStorage.getItem('include_unverified') === 'true'
}

export function setIncludeUnverified(value: boolean) {
  localStorage.setItem('include_unverified', String(value))
}

export function scaleAmount(amount: number, fromMl: number, toMl: number): number {
  const scaled = amount * (toMl / fromMl)
  return Math.round(scaled * 100) / 100
}

export function joinList(items: string[] | null | undefined): string {
  return (items || []).join(', ')
}

export function splitList(value: string): string[] {
  return value
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}
