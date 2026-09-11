import { useTheme } from '@/hooks/useTheme'
import { themedColor } from './palette'
import { formatMoney, formatPercent, toNumber } from '@/utils/format'
import './charts.css'

export interface BarListItem {
  id: string
  name: string
  amount: string | number
  color: string
  /** Participação no total. Calculada aqui quando não vier pronta. */
  percentage?: string | number
}

interface BarListProps {
  items: BarListItem[]
  /** Quando omitido, usa a soma dos itens. */
  total?: string | number
}

/**
 * Magnitude por categoria, em barras horizontais ordenadas.
 *
 * Escolhida no lugar de uma rosca porque comparar comprimentos é mais preciso
 * que comparar ângulos, e porque cada linha traz nome e valor escritos — a
 * identidade nunca depende só da cor.
 */
export function BarList({ items, total }: BarListProps) {
  const { theme } = useTheme()
  const sum = total !== undefined ? toNumber(total) : items.reduce((acc, item) => acc + toNumber(item.amount), 0)
  // A barra mais longa ocupa a largura toda; as outras são proporcionais a ela.
  const largest = items.reduce((max, item) => Math.max(max, toNumber(item.amount)), 0)

  return (
    <div className="bar-list">
      {items.map((item) => {
        const value = toNumber(item.amount)
        const share =
          item.percentage !== undefined ? toNumber(item.percentage) : sum > 0 ? (value / sum) * 100 : 0
        const width = largest > 0 ? (value / largest) * 100 : 0

        return (
          <div key={item.id} className="bar-list__row">
            <div className="bar-list__head">
              <span className="bar-list__label">
                <span
                  className="bar-list__swatch"
                  style={{ backgroundColor: themedColor(item.color, theme) }}
                  aria-hidden="true"
                />
                <span className="bar-list__name">{item.name}</span>
              </span>
              <span className="bar-list__values">
                <span className="bar-list__amount">{formatMoney(value)}</span>
                <span className="bar-list__share">{formatPercent(share)}</span>
              </span>
            </div>
            <div className="bar-list__track">
              <div
                className="bar-list__fill"
                style={{
                  width: `${Math.max(width, value > 0 ? 2 : 0)}%`,
                  backgroundColor: themedColor(item.color, theme),
                }}
              />
            </div>
          </div>
        )
      })}
    </div>
  )
}

interface StackedBarProps {
  segments: Array<{ id: string; label: string; value: string | number; color: string }>
}

/** Distribuição de um todo em uma única barra, com legenda rotulada abaixo. */
export function StackedBar({ segments }: StackedBarProps) {
  const { theme } = useTheme()
  const total = segments.reduce((acc, segment) => acc + toNumber(segment.value), 0)

  if (total <= 0) return null

  return (
    <div>
      <div className="stacked-bar" role="img" aria-label="Distribuição por classe">
        {segments.map((segment) => (
          <div
            key={segment.id}
            className="stacked-bar__segment"
            style={{
              width: `${(toNumber(segment.value) / total) * 100}%`,
              backgroundColor: themedColor(segment.color, theme),
            }}
          />
        ))}
      </div>
      <div className="chart-legend" style={{ marginTop: 'var(--space-4)', marginBottom: 0 }}>
        {segments.map((segment) => (
          <span key={segment.id} className="chart-legend__item">
            <span
              className="chart-legend__swatch"
              style={{ backgroundColor: themedColor(segment.color, theme) }}
              aria-hidden="true"
            />
            {segment.label}
            <span style={{ color: 'var(--text-tertiary)' }}>
              {formatPercent((toNumber(segment.value) / total) * 100)}
            </span>
          </span>
        ))}
      </div>
    </div>
  )
}
