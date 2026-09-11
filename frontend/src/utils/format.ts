/**
 * Formatação de dinheiro e datas.
 *
 * Os valores vêm da API como string decimal. `toNumber` só deve ser usado para
 * exibir ou desenhar gráficos — nunca para armazenar de volta, porque o float
 * do JavaScript não guarda centavos com fidelidade.
 */

const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
})

const compactFormatter = new Intl.NumberFormat('pt-BR', {
  notation: 'compact',
  maximumFractionDigits: 1,
})

export function toNumber(value: string | number | null | undefined): number {
  if (value === null || value === undefined || value === '') return 0
  const parsed = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

export function formatMoney(value: string | number | null | undefined): string {
  return currencyFormatter.format(toNumber(value))
}

/** Versão curta para eixos de gráfico: "R$ 1,2 mil". */
export function formatMoneyCompact(value: string | number | null | undefined): string {
  return `R$ ${compactFormatter.format(toNumber(value))}`
}

/** Prefixa o sinal explicitamente, para receita e despesa se distinguirem. */
export function formatSigned(
  value: string | number | null | undefined,
  type: 'income' | 'expense' | 'transfer',
): string {
  const formatted = formatMoney(value)
  if (type === 'income') return `+ ${formatted}`
  if (type === 'expense') return `− ${formatted}`
  return formatted
}

/**
 * Quantidade de um ativo, sem zeros à direita inúteis.
 *
 * A API devolve 8 casas decimais para caber fração de cripto; mostrar
 * "10,00000000" para dez ações só atrapalha a leitura.
 */
export function formatQuantity(value: string | number | null | undefined): string {
  const parsed = toNumber(value)
  return parsed.toLocaleString('pt-BR', { maximumFractionDigits: 8 })
}

export function formatPercent(value: string | number | null | undefined): string {
  return `${toNumber(value).toLocaleString('pt-BR', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 1,
  })}%`
}

/* -- Datas ------------------------------------------------------------------ */

/**
 * Converte "2026-09-11" em Date local.
 *
 * `new Date("2026-09-11")` é interpretado como UTC e, em fusos negativos como
 * o do Brasil, volta o dia anterior. Montamos os componentes à mão para evitar
 * isso.
 */
export function parseIsoDate(value: string): Date {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(year ?? 1970, (month ?? 1) - 1, day ?? 1)
}

export function toIsoDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function today(): string {
  return toIsoDate(new Date())
}

export function formatDate(value: string): string {
  return parseIsoDate(value).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  })
}

export function formatDateShort(value: string): string {
  return parseIsoDate(value).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
  })
}

export function formatMonth(value: string): string {
  return parseIsoDate(value).toLocaleDateString('pt-BR', {
    month: 'long',
    year: 'numeric',
  })
}

export function formatMonthShort(value: string): string {
  return parseIsoDate(value).toLocaleDateString('pt-BR', { month: 'short' }).replace('.', '')
}

/** "Hoje", "Amanhã", "Ontem" ou a data — o que for mais claro para o leitor. */
export function formatRelativeDay(value: string): string {
  const date = parseIsoDate(value)
  const now = new Date()
  now.setHours(0, 0, 0, 0)
  const diffDays = Math.round((date.getTime() - now.getTime()) / 86_400_000)

  if (diffDays === 0) return 'Hoje'
  if (diffDays === 1) return 'Amanhã'
  if (diffDays === -1) return 'Ontem'
  if (diffDays > 1 && diffDays <= 6) {
    return date.toLocaleDateString('pt-BR', { weekday: 'long' })
  }
  return formatDateShort(value)
}

export function firstDayOfMonth(reference = new Date()): string {
  return toIsoDate(new Date(reference.getFullYear(), reference.getMonth(), 1))
}

export function addMonths(value: string, months: number): string {
  const date = parseIsoDate(value)
  const targetDay = date.getDate()
  const shifted = new Date(date.getFullYear(), date.getMonth() + months, 1)
  const lastDay = new Date(shifted.getFullYear(), shifted.getMonth() + 1, 0).getDate()
  shifted.setDate(Math.min(targetDay, lastDay))
  return toIsoDate(shifted)
}

/** Primeiro nome, para a saudação do dashboard. */
export function firstName(fullName: string | null, fallback: string): string {
  const trimmed = fullName?.trim()
  if (!trimmed) return fallback
  return trimmed.split(/\s+/)[0] ?? fallback
}

/* -- Rótulos ----------------------------------------------------------------- */

export const ACCOUNT_TYPE_LABELS: Record<string, string> = {
  checking: 'Conta corrente',
  savings: 'Poupança',
  investment: 'Investimento',
  cash: 'Dinheiro',
}

export const CARD_BRAND_LABELS: Record<string, string> = {
  visa: 'Visa',
  mastercard: 'Mastercard',
  elo: 'Elo',
  amex: 'Amex',
  hipercard: 'Hipercard',
  other: 'Outra',
}

export const INVESTMENT_TYPE_LABELS: Record<string, string> = {
  stock: 'Ações',
  fii: 'FIIs',
  crypto: 'Cripto',
  fixed_income: 'Renda fixa',
  treasury: 'Tesouro',
  etf: 'ETF',
  other: 'Outros',
}

export const FREQUENCY_LABELS: Record<string, string> = {
  daily: 'Diária',
  weekly: 'Semanal',
  monthly: 'Mensal',
  yearly: 'Anual',
}

export const TRANSACTION_TYPE_LABELS: Record<string, string> = {
  income: 'Receita',
  expense: 'Despesa',
  transfer: 'Transferência',
}

export const INVOICE_STATUS_LABELS: Record<string, string> = {
  open: 'Aberta',
  closed: 'Fechada',
  due: 'Vencida',
}
