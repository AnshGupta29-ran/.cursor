import type { Transaction, TransactionFormData, Budget, Summary, Insights, PaginatedResponse } from './types'

const BASE = '/api'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  // Transactions
  getTransactions(params?: {
    page?: number
    per_page?: number
    category?: string
    type?: string
    month?: number
    year?: number
    search?: string
  }): Promise<PaginatedResponse<Transaction>> {
    const q = new URLSearchParams()
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== '') q.set(k, String(v))
      })
    }
    return request(`/transactions?${q}`)
  },

  createTransaction(data: TransactionFormData): Promise<Transaction> {
    return request('/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  deleteTransaction(id: number): Promise<{ message: string }> {
    return request(`/transactions/${id}`, { method: 'DELETE' })
  },

  // Summary
  getSummary(month?: number, year?: number): Promise<Summary> {
    const q = new URLSearchParams()
    if (month) q.set('month', String(month))
    if (year) q.set('year', String(year))
    return request(`/summary?${q}`)
  },

  // Insights
  getInsights(): Promise<Insights> {
    return request('/insights')
  },

  // Budgets
  getBudgets(month?: number, year?: number): Promise<Budget[]> {
    const q = new URLSearchParams()
    if (month) q.set('month', String(month))
    if (year) q.set('year', String(year))
    return request(`/budgets?${q}`)
  },

  createBudget(data: { category: string; amount: number; month: number; year: number }): Promise<Budget> {
    return request('/budgets', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  updateBudget(id: number, data: { amount: number }): Promise<Budget> {
    return request(`/budgets/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  },

  deleteBudget(id: number): Promise<{ message: string }> {
    return request(`/budgets/${id}`, { method: 'DELETE' })
  },

  // Categories
  getCategories(): Promise<{ categories: string[]; subcategories: Record<string, string[]> }> {
    return request('/categories')
  },
}
