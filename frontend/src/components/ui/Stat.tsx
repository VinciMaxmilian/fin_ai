import type { ReactNode } from 'react'
import { GlassCard } from './GlassCard'
import { Skeleton } from './Feedback'
import { cx } from '@/utils/cx'
import './page.css'

interface StatProps {
  label: string
  value: string
  hint?: ReactNode
  /** Ícone com fundo suave, à esquerda do rótulo. */
  icon?: ReactNode
  iconColor?: string
  iconBackground?: string
  tone?: 'default' | 'positive' | 'negative'
  large?: boolean
  loading?: boolean
}

/**
 * Um número com contexto. Existe para o caso em que um gráfico não acrescenta
 * nada: quando a resposta é um valor só, mostre o valor.
 */
export function Stat({
  label,
  value,
  hint,
  icon,
  iconColor,
  iconBackground,
  tone = 'default',
  large = false,
  loading = false,
}: StatProps) {
  return (
    <GlassCard compact>
      <div className="stat">
        <span className="stat__label">
          {icon && (
            <span
              className="stat__icon"
              style={{ color: iconColor, backgroundColor: iconBackground }}
              aria-hidden="true"
            >
              {icon}
            </span>
          )}
          {label}
        </span>

        {loading ? (
          <Skeleton width="65%" height={large ? 34 : 28} />
        ) : (
          <span
            className={cx(
              'stat__value',
              large && 'stat__value--lg',
              tone === 'positive' && 'text-positive',
              tone === 'negative' && 'text-negative',
            )}
          >
            {value}
          </span>
        )}

        {hint && !loading && <span className="stat__hint">{hint}</span>}
      </div>
    </GlassCard>
  )
}

interface SegmentedProps<T extends string> {
  options: Array<{ value: T; label: string }>
  value: T
  onChange: (value: T) => void
  ariaLabel: string
}

/** Seletor compacto de opções mutuamente exclusivas. Usado para períodos. */
export function Segmented<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
}: SegmentedProps<T>) {
  return (
    <div className="segmented" role="group" aria-label={ariaLabel}>
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          className={cx(
            'segmented__option',
            option.value === value && 'segmented__option--active',
          )}
          aria-pressed={option.value === value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
