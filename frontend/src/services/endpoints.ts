/**
 * Todas as chamadas à API, agrupadas por módulo.
 *
 * Nenhum componente monta URL na mão: quando uma rota muda, muda aqui e só
 * aqui.
 */
import { api } from './client'
import type { QueryParams } from './client'
import type {
  Account,
  AssetSearchResult,
  AccountsSummary,
  BudgetSummary,
  Card,
  CardSpending,
  CashFlow,
  CategoryBreakdown,
  Category,
  Dashboard,
  DividendPayment,
  Goal,
  HistoricalPoint,
  InstallmentPlan,
  Investment,
  Invoice,
  IsoDate,
  MarketCapabilities,
  MonthlySeries,
  NetWorthPoint,
  Occurrence,
  Overview,
  Page,
  Period,
  Portfolio,
  Quote,
  RecurringRule,
  RecurringSummary,
  Transaction,
  TransactionInput,
  TransactionQuery,
  UUID,
  UpcomingBill,
  User,
} from '@/types/api'

export const usersApi = {
  me: () => api.get<User>('/users/me'),
  update: (data: Partial<Pick<User, 'full_name' | 'currency' | 'locale'>>) =>
    api.patch<User>('/users/me', data),
}

export const accountsApi = {
  list: (includeArchived = false) =>
    api.get<AccountsSummary>('/accounts', { include_archived: includeArchived }),
  create: (data: Record<string, unknown>) => api.post<Account>('/accounts', data),
  update: (id: UUID, data: Record<string, unknown>) =>
    api.patch<Account>(`/accounts/${id}`, data),
  remove: (id: UUID) => api.delete(`/accounts/${id}`),
}

export const cardsApi = {
  list: (includeArchived = false) =>
    api.get<Card[]>('/cards', { include_archived: includeArchived }),
  create: (data: Record<string, unknown>) => api.post<Card>('/cards', data),
  update: (id: UUID, data: Record<string, unknown>) => api.patch<Card>(`/cards/${id}`, data),
  remove: (id: UUID) => api.delete(`/cards/${id}`),
  invoices: (id: UUID, months = 6) =>
    api.get<Invoice[]>(`/cards/${id}/invoices`, { months }),
}

export const categoriesApi = {
  list: (kind?: 'expense' | 'income') =>
    api.get<Category[]>('/categories', kind ? { kind } : undefined),
  create: (data: Record<string, unknown>) => api.post<Category>('/categories', data),
  update: (id: UUID, data: Record<string, unknown>) =>
    api.patch<Category>(`/categories/${id}`, data),
  remove: (id: UUID) => api.delete(`/categories/${id}`),
}

export const transactionsApi = {
  list: (query: TransactionQuery = {}, signal?: AbortSignal) =>
    api.get<Page<Transaction>>('/transactions', query as QueryParams, signal),
  create: (data: TransactionInput) => api.post<Transaction[]>('/transactions', data),
  update: (id: UUID, data: Partial<TransactionInput>) =>
    api.patch<Transaction>(`/transactions/${id}`, data),
  remove: (id: UUID) => api.delete(`/transactions/${id}`),
}

export const recurringApi = {
  list: (onlyActive = false) =>
    api.get<RecurringRule[]>('/recurring', { only_active: onlyActive }),
  create: (data: Record<string, unknown>) => api.post<RecurringRule>('/recurring', data),
  update: (id: UUID, data: Record<string, unknown>) =>
    api.patch<RecurringRule>(`/recurring/${id}`, data),
  remove: (id: UUID) => api.delete(`/recurring/${id}`),
  occurrences: (dateFrom: IsoDate, dateTo: IsoDate) =>
    api.get<Occurrence[]>('/recurring/occurrences', {
      date_from: dateFrom,
      date_to: dateTo,
    }),
  confirm: (id: UUID, dueDate: IsoDate) =>
    api.post<Transaction>(`/recurring/${id}/confirm`, { due_date: dueDate }),
}

export const budgetsApi = {
  summary: (month: IsoDate) => api.get<BudgetSummary>('/budgets', { month }),
  set: (month: IsoDate, categoryId: UUID, amount: string) =>
    api.put('/budgets', { month, category_id: categoryId, amount }),
  copyPrevious: (month: IsoDate) =>
    api.post<BudgetSummary>('/budgets/copy-previous', undefined, { month }),
  remove: (id: UUID) => api.delete(`/budgets/${id}`),
}

export const goalsApi = {
  list: (includeArchived = false) =>
    api.get<Goal[]>('/goals', { include_archived: includeArchived }),
  create: (data: Record<string, unknown>) => api.post<Goal>('/goals', data),
  update: (id: UUID, data: Record<string, unknown>) => api.patch<Goal>(`/goals/${id}`, data),
  contribute: (id: UUID, amount: string) =>
    api.post<Goal>(`/goals/${id}/contributions`, { amount }),
  remove: (id: UUID) => api.delete(`/goals/${id}`),
}

export const installmentsApi = {
  list: (onlyOpen = false) =>
    api.get<InstallmentPlan[]>('/installments', { only_open: onlyOpen }),
  transactions: (id: UUID) => api.get<Transaction[]>(`/installments/${id}/transactions`),
  remove: (id: UUID) => api.delete(`/installments/${id}`),
}

export const investmentsApi = {
  portfolio: () => api.get<Portfolio>('/investments'),
  /** Descarta o cache de cotacoes no servidor e busca de novo. */
  refresh: () => api.post<Portfolio>('/investments/refresh'),
  create: (data: Record<string, unknown>) => api.post<Investment>('/investments', data),
  update: (id: UUID, data: Record<string, unknown>) =>
    api.patch<Investment>(`/investments/${id}`, data),
  remove: (id: UUID) => api.delete(`/investments/${id}`),
}

/**
 * Dados de mercado.
 *
 * Tudo passa pelo nosso backend: o token da brapi e segredo de servidor e
 * nunca chega ao navegador.
 */
export const marketApi = {
  capabilities: () => api.get<MarketCapabilities>('/investments/market/capabilities'),
  search: (term: string, signal?: AbortSignal) =>
    api.get<AssetSearchResult[]>('/investments/market/search', { term }, signal),
  quote: (ticker: string) => api.get<Quote>(`/investments/market/${ticker}/quote`),
  history: (ticker: string, range = '1mo', interval = '1d') =>
    api.get<HistoricalPoint[]>(`/investments/market/${ticker}/history`, { range, interval }),
  dividends: (ticker: string, limit = 24) =>
    api.get<DividendPayment[]>(`/investments/market/${ticker}/dividends`, { limit }),
}

export const reportsApi = {
  dashboard: (period: Period = '30d') =>
    api.get<Dashboard>('/reports/dashboard', { period }),
  overview: () => api.get<Overview>('/reports/overview'),
  cashFlow: (period: Period) => api.get<CashFlow>('/reports/cash-flow', { period }),
  expensesByCategory: (dateFrom?: IsoDate, dateTo?: IsoDate, limit?: number) =>
    api.get<CategoryBreakdown>('/reports/expenses-by-category', {
      date_from: dateFrom,
      date_to: dateTo,
      limit,
    }),
  upcomingBills: (days = 30) => api.get<UpcomingBill[]>('/reports/upcoming-bills', { days }),
  monthly: (months = 12) => api.get<MonthlySeries>('/reports/monthly', { months }),
  netWorth: (months = 12) =>
    api.get<{ points: NetWorthPoint[] }>('/reports/net-worth', { months }),
  cardSpending: (dateFrom?: IsoDate, dateTo?: IsoDate) =>
    api.get<CardSpending>('/reports/card-spending', {
      date_from: dateFrom,
      date_to: dateTo,
    }),
  recurring: () => api.get<RecurringSummary>('/reports/recurring'),
}
