import { useMemo, useState } from 'react'
import { useElementWidth } from '@/hooks/useElementWidth'
import { formatMoney, formatMoneyCompact } from '@/utils/format'
import './charts.css'

export interface BarSeries {
  id: string
  label: string
  color: string
  values: number[]
}

interface GroupedBarsProps {
  labels: string[]
  series: BarSeries[]
  height?: number
  ariaLabel: string
}

const PADDING = { top: 16, right: 8, bottom: 26, left: 56 }
const GRID_LINES = 4
/** Respiro entre barras do mesmo grupo, na cor da superfície. */
const BAR_GAP = 2
const GROUP_GAP_RATIO = 0.34

/** Comparação de duas ou três séries mês a mês. */
export function GroupedBars({ labels, series, height = 260, ariaLabel }: GroupedBarsProps) {
  const { ref: wrapperRef, width } = useElementWidth()
  const [hoverIndex, setHoverIndex] = useState<number | null>(null)

  const geometry = useMemo(() => {
    const max = Math.max(...series.flatMap((item) => item.values), 0) * 1.08 || 100
    const plotWidth = Math.max(width - PADDING.left - PADDING.right, 10)
    const plotHeight = height - PADDING.top - PADDING.bottom
    const groupWidth = plotWidth / Math.max(labels.length, 1)
    const usableWidth = groupWidth * (1 - GROUP_GAP_RATIO)
    const barWidth = Math.max((usableWidth - BAR_GAP * (series.length - 1)) / series.length, 3)

    return {
      max,
      plotHeight,
      groupWidth,
      barWidth,
      usableWidth,
      baseline: PADDING.top + plotHeight,
      groupX: (index: number) => PADDING.left + index * groupWidth,
      y: (value: number) => PADDING.top + plotHeight - (value / max) * plotHeight,
    }
  }, [series, labels.length, width, height])

  const ticks = Array.from({ length: GRID_LINES + 1 }, (_, index) => {
    const value = (geometry.max / GRID_LINES) * index
    return { value, y: geometry.y(value) }
  })

  const labelStep = Math.max(1, Math.ceil(labels.length / (width < 520 ? 4 : 12)))

  return (
    <div className="chart" ref={wrapperRef}>
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

        <line
          className="chart__baseline"
          x1={PADDING.left}
          x2={width - PADDING.right}
          y1={geometry.baseline}
          y2={geometry.baseline}
        />

        {labels.map((label, groupIndex) => {
          const startX =
            geometry.groupX(groupIndex) + (geometry.groupWidth - geometry.usableWidth) / 2

          return (
            <g
              key={`${label}-${groupIndex}`}
              className="chart__bar-group"
              onMouseEnter={() => setHoverIndex(groupIndex)}
              onMouseLeave={() => setHoverIndex(null)}
            >
              <rect
                className="chart__hit"
                x={geometry.groupX(groupIndex)}
                y={PADDING.top}
                width={geometry.groupWidth}
                height={geometry.plotHeight}
              />
              {series.map((item, seriesIndex) => {
                const value = item.values[groupIndex] ?? 0
                const barHeight = Math.max(geometry.baseline - geometry.y(value), value > 0 ? 2 : 0)
                return (
                  <rect
                    key={item.id}
                    className="chart__bar"
                    x={startX + seriesIndex * (geometry.barWidth + BAR_GAP)}
                    y={geometry.baseline - barHeight}
                    width={geometry.barWidth}
                    height={barHeight}
                    fill={item.color}
                    /* Ponta arredondada de 4px, ancorada na linha de base. */
                    rx={Math.min(4, geometry.barWidth / 2)}
                  />
                )
              })}
              {groupIndex % labelStep === 0 && (
                <text
                  className="chart__axis-label"
                  x={geometry.groupX(groupIndex) + geometry.groupWidth / 2}
                  y={height - 6}
                  textAnchor="middle"
                >
                  {label}
                </text>
              )}
            </g>
          )
        })}
      </svg>

      {hoverIndex !== null && (
        <div
          className="chart-tooltip"
          style={{
            left: geometry.groupX(hoverIndex) + geometry.groupWidth / 2,
            top: PADDING.top,
          }}
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
