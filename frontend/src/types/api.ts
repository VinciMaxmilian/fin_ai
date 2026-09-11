/**
 * Espelho dos schemas do backend.
 *
 * Valores monetários chegam como string para não perder centavos no float do
 * JavaScript. Converta com `toNumber` (utils/format) só na hora de calcular ou
 * desenhar, nunca para guardar.
 */

export type UUID = string
/** Decimal serializado, ex.: "1234.56". */
export type Money = string
/** Data ISO, ex.: "2026-09-11". */
export type IsoDate = string

export type TransactionType = 'income' | 'expense' | 'transfer'
export type AccountType = 'checking' | 'savings' | 'investment' | 'cash'
/** Como a conta remunera o saldo. */
export type YieldType = 'none' | 'cdi_percent'
export type CardBrand = 'visa' | 'mastercard' | 'elo' | 'amex' | 'hipercard' | 'other'
export type CategoryKind = 'expense' | 'income' | 'both'
export type Frequency = 'daily' | 'weekly' | 'monthly' | 'yearly'
export type InvestmentType =
  | 'stock'
  | 'fii'
  | 'crypto'
  | 'fixed_income'
  | 'treasury'
  | 'etf'
  | 'other'
export type Period = '7d' | '30d' | '3m' | '6m' | '1y'
export type InvoiceStatus = 'open' | 'closed' | 'due'

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface User {
  id: UUID
  email: string
  full_name: string | null
  avatar_url: string | null
  currency: string
  locale: string
  created_at: string
}

export interface YieldInfo {
  /** Rendimento já acumulado no mês corrente, ainda não creditado. */
  projected_amount: Money
  projected_month: IsoDate
  business_days: number
  last_credited_month: IsoDate | null
  /** null quando a fonte da taxa está fora do ar. */
  annual_rate: Money | null
}

export interface Account {
  id: UUID
  name: string
  bank: string | null
  type: AccountType
  initial_balance: Money
  current_balance: Money
  color: string
  icon: string
  is_archived: boolean
  created_at: string
  yield_type: YieldType
  /** Percentual do índice: 100 = 100% do CDI. */
  yield_rate: Money
  yield_started_on: IsoDate | null
  last_yield_month: IsoDate | null
  yield_info: YieldInfo | null
}

export interface AccountsSummary {
  total_balance: Money
  accounts: Account[]
  cdi_annual_rate: Money | null
}

export interface Invoice {
  card_id: UUID
  period_start: IsoDate
  period_end: IsoDate
  closing_date: IsoDate
  due_date: IsoDate
  total: Money
  transactions_count: number
  status: InvoiceStatus
}

export interface Card {
  id: UUID
  name: string
  bank: string | null
  brand: CardBrand
  limit_amount: Money
  closing_day: number
  due_day: number
  account_id: UUID | null
  color: string
  is_archived: boolean
  created_at: string
  used_limit: Money
  available_limit: Money
  current_invoice: Invoice | null
}

export interface Category {
  id: UUID
  name: string
  kind: CategoryKind
  color: string
  icon: string
  parent_id: UUID | null
  is_system: boolean
  created_at: string
}

export interface CategoryRef {
  id: UUID
  name: string
  color: string
  icon: string
}

export interface Transaction {
  id: UUID
  type: TransactionType
  amount: Money
  description: string
  date: IsoDate
  category_id: UUID | null
  account_id: UUID | null
  card_id: UUID | null
  transfer_account_id: UUID | null
  notes: string | null
  installment_plan_id: UUID | null
  installment_number: number | null
  recurring_rule_id: UUID | null
  category: CategoryRef | null
  created_at: string
  updated_at: string
}

export interface TransactionInput {
  type: TransactionType
  amount: string
  description: string
  date: IsoDate
  category_id?: UUID | null
  account_id?: UUID | null
  card_id?: UUID | null
  transfer_account_id?: UUID | null
  notes?: string | null
  installments?: number
}

export interface TransactionQuery {
  search?: string
  type?: TransactionType
  category_id?: UUID
  account_id?: UUID
  card_id?: UUID
  date_from?: IsoDate
  date_to?: IsoDate
  amount_min?: string
  amount_max?: string
  sort_by?: 'date' | 'amount' | 'description' | 'created_at'
  sort_order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export interface RecurringRule {
  id: UUID
  description: string
  amount: Money
  type: TransactionType
  frequency: Frequency
  day_of_month: number | null
  weekday: number | null
  month_of_year: number | null
  start_date: IsoDate
  end_date: IsoDate | null
  is_active: boolean
  category_id: UUID | null
  account_id: UUID | null
  card_id: UUID | null
  notes: string | null
  created_at: string
}

export interface Occurrence {
  rule_id: UUID
  description: string
  amount: Money
  type: TransactionType
  due_date: IsoDate
  category_id: UUID | null
  account_id: UUID | null
  card_id: UUID | null
  is_settled: boolean
}

export interface BudgetItem {
  id: UUID
  month: IsoDate
  category_id: UUID
  category_name: string
  category_color: string
  category_icon: string
  amount: Money
  spent: Money
  remaining: Money
  used_percentage: Money
  is_exceeded: boolean
}

export interface BudgetSummary {
  month: IsoDate
  total_planned: Money
  total_spent: Money
  total_remaining: Money
  used_percentage: Money
  items: BudgetItem[]
}

export interface Goal {
  id: UUID
  name: string
  target_amount: Money
  current_amount: Money
  target_date: IsoDate | null
  color: string
  icon: string
  notes: string | null
  progress: Money
  remaining: Money
  is_completed: boolean
  is_archived: boolean
  created_at: string
}

export interface InstallmentPlan {
  id: UUID
  description: string
  total_amount: Money
  installments_count: number
  installment_amount: Money
  first_due_date: IsoDate
  card_id: UUID | null
  account_id: UUID | null
  category_id: UUID | null
  notes: string | null
  paid_installments: number
  remaining_installments: number
  paid_amount: Money
  remaining_amount: Money
  next_due_date: IsoDate | null
  is_completed: boolean
  created_at: string
}

/** De onde veio o preco usado no calculo desta posicao. */
export type PriceSource = 'quote' | 'stale_quote' | 'manual' | 'average_price'

export interface Investment {
  id: UUID
  asset: string
  /** Codigo de negociacao. Preenchido, a cotacao e buscada automaticamente. */
  ticker: string | null
  type: InvestmentType
  quantity: string
  average_price: Money
  current_price: Money
  institution: string | null
  notes: string | null
  invested_amount: Money
  current_value: Money
  profit: Money
  profitability: Money
  price_source: PriceSource
  quote_age_seconds: number | null
  day_change: Money | null
  day_change_percent: Money | null
  long_name: string | null
  logo_url: string | null
  created_at: string
}

export interface MarketDataStatus {
  provider: string | null
  enabled: boolean
  quoted_positions: number
  oldest_quote_age_seconds: number | null
  has_stale_quotes: boolean
  crypto_supported: boolean
}

export interface Quote {
  symbol: string
  price: Money
  currency: string
  short_name: string | null
  long_name: string | null
  change: Money | null
  change_percent: Money | null
  day_open: Money | null
  day_high: Money | null
  day_low: Money | null
  previous_close: Money | null
  volume: number | null
  market_cap: number | null
  fifty_two_week_low: Money | null
  fifty_two_week_high: Money | null
  logo_url: string | null
  quoted_at: string | null
  age_seconds: number
  is_stale: boolean
}

export interface HistoricalPoint {
  date: IsoDate
  open: Money
  high: Money
  low: Money
  close: Money
  adjusted_close: Money | null
  volume: number | null
}

export interface DividendPayment {
  payment_date: IsoDate | null
  rate: Money
  label: string | null
  last_date_prior: IsoDate | null
}

export interface AssetSearchResult {
  symbol: string
  kind: string
}

export interface MarketCapabilities {
  provider: string | null
  enabled: boolean
  quotes: boolean
  history: boolean
  dividends: boolean
  search: boolean
  crypto: boolean
  notes: Record<string, string>
}

export interface AllocationSlice {
  type: string
  label: string
  value: Money
  percentage: Money
}

export interface Portfolio {
  invested_amount: Money
  current_value: Money
  profit: Money
  profitability: Money
  allocation: AllocationSlice[]
  positions: Investment[]
  market_data: MarketDataStatus
}

export interface Overview {
  reference_month: IsoDate
  net_worth: Money
  available_balance: Money
  invested_amount: Money
  open_invoices: Money
  income: Money
  expenses: Money
  balance: Money
}

export interface CashFlowPoint {
  date: IsoDate
  income: Money
  expenses: Money
  balance: Money
}

export interface CashFlow {
  period: string
  granularity: 'day' | 'month'
  start_date: IsoDate
  end_date: IsoDate
  total_income: Money
  total_expenses: Money
  total_balance: Money
  points: CashFlowPoint[]
}

export interface CategorySlice {
  category_id: UUID | null
  name: string
  color: string
  icon: string
  amount: Money
  percentage: Money
}

export interface CategoryBreakdown {
  start_date: IsoDate
  end_date: IsoDate
  total: Money
  items: CategorySlice[]
}

export interface UpcomingBill {
  kind: 'recurring' | 'card_invoice'
  reference_id: UUID
  description: string
  amount: Money
  due_date: IsoDate
}

export interface Dashboard {
  overview: Overview
  cash_flow: CashFlow
  expenses_by_category: CategoryBreakdown
  upcoming_bills: UpcomingBill[]
  cards: Card[]
}

export interface MonthlyPoint {
  month: IsoDate
  income: Money
  expenses: Money
  balance: Money
  cumulative_balance: Money
}

export interface MonthlySeries {
  start_date: IsoDate
  end_date: IsoDate
  points: MonthlyPoint[]
}

export interface NetWorthPoint {
  month: IsoDate
  accounts_balance: Money
  invested_amount: Money
  net_worth: Money
}

export interface CardSlice {
  card_id: UUID
  name: string
  color: string
  amount: Money
  percentage: Money
}

export interface CardSpending {
  start_date: IsoDate
  end_date: IsoDate
  total: Money
  items: CardSlice[]
}

export interface RecurringSummary {
  month: IsoDate
  recurring_income: Money
  recurring_expenses: Money
  net: Money
  items: Array<{
    rule_id: UUID
    description: string
    amount: Money
    type: TransactionType
    due_date: IsoDate
    is_settled: boolean
  }>
}
