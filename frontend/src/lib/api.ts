import type { CombinationRequest, Ingredient, Recipe, SuggestedFormulation, VerificationQueueItem } from '../types'

const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      const d = body.detail
      if (typeof d === 'object' && d !== null && 'error' in d) {
        detail = d.suggestion ? `${d.error} ${d.suggestion}` : d.error
      } else if (typeof d === 'string') {
        detail = d
      } else if (d) {
        detail = JSON.stringify(d)
      }
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
  }
  if (res.status === 204) return undefined as T
  return res.json()
}

function qs(params: Record<string, string | boolean | undefined>) {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== '') q.set(k, String(v))
  }
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const api = {
  listIngredients: (params: Record<string, string | boolean | undefined> = {}) =>
    request<Ingredient[]>(`/ingredients${qs(params)}`),

  getIngredient: (id: string) => request<Ingredient>(`/ingredients/${id}`),

  createIngredient: (data: Partial<Ingredient>) =>
    request<Ingredient>('/ingredients', { method: 'POST', body: JSON.stringify(data) }),

  updateIngredient: (id: string, data: Partial<Ingredient>) =>
    request<Ingredient>(`/ingredients/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteIngredient: (id: string) =>
    request<void>(`/ingredients/${id}`, { method: 'DELETE' }),

  verificationQueue: () => request<VerificationQueueItem[]>('/ingredients/verification-queue'),

  listRecipes: (params: Record<string, string | undefined> = {}) =>
    request<Recipe[]>(`/recipes${qs(params)}`),

  getRecipe: (id: string) => request<Recipe>(`/recipes/${id}`),

  createRecipe: (data: Partial<Recipe>) =>
    request<Recipe>('/recipes', { method: 'POST', body: JSON.stringify(data) }),

  updateRecipe: (id: string, data: Partial<Recipe>) =>
    request<Recipe>(`/recipes/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteRecipe: (id: string) =>
    request<void>(`/recipes/${id}`, { method: 'DELETE' }),

  suggestCombinations: (body: CombinationRequest) =>
    request<{ formulations: SuggestedFormulation[]; candidate_pool_size: number; exploratory_mode: boolean }>(
      '/combinations/suggest',
      { method: 'POST', body: JSON.stringify(body) },
    ),
}
