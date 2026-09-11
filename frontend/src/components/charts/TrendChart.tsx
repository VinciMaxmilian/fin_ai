import { useMemo, useState } from 'react'
import { useElementWidth } from '@/hooks/useElementWidth'
import { formatMoney, formatMoneyCompact } from '@/utils/format'
import './charts.css'

export interface TrendSeries {
  id: string
  label: string
  color: string
  values: number[]
  /** Preenche a área sob a linha. Use em no máximo uma série por gráfico. */
  area?: boolean
}

interface TrendChartProps {
  labels: string[]
  series: TrendSeries[]
  height?: number
  /** Texto que nomeia o eixo horizontal para leitores de tela. */
  ariaLabel: string
}

const PADDING = { top: 16, right: 8, bottom: 26, left: 56 }
const GRID_LINES = 4

/**
 * Série temporal em linhas, com área opcional.
 *
 * Um único eixo de valores, sempre — duas escalas no mesmo gráfico é a
 * principal fonte de leitura errada em painéis financeiros.
 */
export function TrendChart({ labels, series, height = 240, ariaLabel }: TrendChartProps) {
  const { ref: wrapperRef, width } = useElementWidth()
  const [hoverIndex, setHoverIndex] = useState<number | null>(null)

  const geometry = useMemo(() => {
    const allValues = series.flatMap((item) => item.values)
    const rawMax = Math.max(...allValues, 0)
    const rawMin = Math.min(...allValues, 0)
    // Folga no topo para a linha não encostar na borda.
    const max = rawMax === 0 && rawMin === 0 ? 100 : rawMax * 1.08
    const min = rawMin < 0 ? rawMin * 1.08 : 0

    const plotWidth = Math.max(width - PADDING.left - PADDING.right, 10)
    const plotHeight = height - PADDING.top - PADDING.bottom
    const count = labels.length

    const x = (index: number) =>
      PADDING.left + (count <= 1 ? plotWidth / 2 : (index / (count - 1)) * plotWidth)
    const y = (value: number) =>
      PADDING.top + plotHeight - ((value - min) / (max - min || 1)) * plotHeight

    return { x, y, max, min, plotWidth, plotHeight, baseline: y(Math.max(min, 0)) }
  }, [series, labels.length, width, height])

  const ticks = useMemo(() => {
    const { max, min } = geometry
    return Array.from({ length: GRID_LINES + 1 }, (_, index) => {
      const value = min + ((max - min) / GRID_LINES) * index
      return { value, y: geometry.y(value) }
    })
  }, [geometry])

  // Mostra poucos rótulos no eixo: o suficiente para orientar, sem empilhar.
  const labelStep = Math.max(1, Math.ceil(labels.length / (width < 520 ? 4 : 7)))

  const buildPath = (values: number[]) =>
    values.map((value, index) => `${index === 0 ? 'M' : 'L'}${geometry.x(index)},${geometry.y(value)}`).join(' ')

  const buildArea = (values: number[]) => {
    if (values.length === 0) return ''
    const line = buildPath(values)
    const lastX = geometry.x(values.length - 1)
    const firstX = geometry.x(0)
    return `${line} L${lastX},${geometry.baseline} L${firstX},${geometry.baseline} Z`
  }

  const handleMove = (event: React.MouseEvent<SVGRectElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect()
    const offset = event.clientX - bounds.left
    const ratio = offset / bounds.width
    const index = Math.round(ratio * (labels.length - 1))
    setHoverIndex(Math.max(0, Math.min(labels.length - 1, index)))
  }

  const hasData = labels.length > 0 && series.some((item) => item.values.some((value) => value !== 0))

  return (
    <div className="chart" ref={wrapperRef}>
      {series.length > 1 && (
        <div className="chart-legend">
          {series.map((item) => (
            <span key={item.id} className="chart-legend__item">
              <span
                className="chart-legend__swatch"
                style={{ backgroundColor: item.color }}
                aria-hidden="true"
              />
              {item.label}
            </span>
          ))}
        </div>
      )}

      <svg
        className="chart__svg"
        viewBox={`0 0 ${width} ${height}`}
        height={height}
        role="img"
        aria-label={ariaLabel}
      >
        {ticks.map((tick) => (
          <g key={tick.value}>
            <line
              className="chart__grid-line"
              x1={PADDING.left}
              x2={width - PADDING.right}
              y1={tick.y}
              y2={tick.y}
            />
            <text className="chart__axis-label" x={PADDING.left - 10} y={tick.y + 4} textAnchor="end">
              {formatMoneyCompact(tick.value)}
            </text>
          </g>
        ))}

        {labels.map((label, index) =>
          index % labelStep === 0 ? (
            <text
              key={`${label}-${index}`}
              className="chart__axis-label"
              x={geometry.x(index)}
              y={height - 6}
              textAnchor="middle"
            >
              {label}
            </text>
          ) : null,
        )}

        {hasData &&
          series.map((item) =>
            item.area ? (
              <path
                key={`${item.id}-area`}
                d={buildArea(item.values)}
                fill={item.color}
                opacity={0.1}
              />
            ) : null,
          )}

        {hasData &&
          series.map((item) => (
            <path key={item.id} className="chart__line" d={buildPath(item.values)} stroke={item.color} />
          ))}

        {hoverIndex !== null && hasData && (
          <>
            <line
              className="chart__crosshair"
              x1={geometry.x(hoverIndex)}
              x2={geometry.x(hoverIndex)}
              y1={PADDING.top}
              y2={height - PADDING.bottom}
            />
            {series.map((item) => (
              <circle
                key={`${item.id}-marker`}
                className="chart__marker"
                cx={geometry.x(hoverIndex)}
                cy={geometry.y(item.values[hoverIndex] ?? 0)}
                r={4.5}
                fill={item.color}
              />
            ))}
          </>
        )}

        <rect
          className="chart__hit"
          x={PADDING.left}
          y={PADDING.top}
          width={geometry.plotWidth}
          height={geometry.plotHeight}
          onMouseMove={handleMove}
          onMouseLeave={() => setHoverIndex(null)}
        />
      </svg>

      {hoverIndex !== null && hasData && (
        <div
          className="chart-tooltip"
          style={{ left: geometry.x(hoverIndex), top: PADDING.top }}
        >
          <p className="chart-tooltip__title">{labels[hoverIndex]}</p>
          {series.map((item) => (
            <div key={item.id} className="chart-tooltip__row">
              <span className="chart-tooltip__label">
                <span
                  className="chart-legend__swatch"
                  style={{ backgroundColor: item.color }}
                  aria-hidden="true"
                />
                {item.label}
              </span>
              <span className="chart-tooltip__value">{formatMoney(item.values[hoverIndex] ?? 0)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
