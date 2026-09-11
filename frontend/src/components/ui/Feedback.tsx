import type { CSSProperties, ReactNode } from 'react'
import { cx } from '@/utils/cx'
import './feedback.css'

/* -- Skeleton --------------------------------------------------------------- */

interface SkeletonProps {
  width?: string | number
  height?: string | number
  radius?: string
  className?: string
}

export function Skeleton({ width = '100%', height = 16, radius, className }: SkeletonProps) {
  const style: CSSProperties = { width, height }
  if (radius) style.borderRadius = radius
  return <div className={cx('skeleton', className)} style={style} aria-hidden="true" />
}

/** Várias linhas de skeleton, com a última mais curta — como um parágrafo real. */
export function SkeletonLines({ count = 3 }: { count?: number }) {
  return (
    <div className="skeleton-stack" aria-hidden="true">
      {Array.from({ length: count }, (_, index) => (
        <Skeleton key={index} width={index === count - 1 ? '60%' : '100%'} />
      ))}
    </div>
  )
}

/* -- Estado vazio ----------------------------------------------------------- */

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  message?: string
  action?: ReactNode
  compact?: boolean
}

export function EmptyState({ icon, title, message, action, compact }: EmptyStateProps) {
  return (
    <div className={cx('empty-state', compact && 'empty-state--compact')}>
      {icon && <div className="empty-state__art">{icon}</div>}
      <p className="empty-state__title">{title}</p>
      {message && <p className="empty-state__message">{message}</p>}
      {action && <div className="empty-state__action">{action}</div>}
    </div>
  )
}

/* -- Erro -------------------------------------------------------------------- */

interface ErrorNoticeProps {
  title?: string
  /** Mensagem já legível para quem usa o app, não o stack trace. */
  detail?: string
  action?: ReactNode
}

export function ErrorNotice({
  title = 'Não foi possível carregar',
  detail,
  action,
}: ErrorNoticeProps) {
  return (
    <div className="error-notice" role="alert">
      <svg
        className="error-notice__icon"
        width="18"
        height="18"
        viewBox="0 0 18 18"
        aria-hidden="true"
      >
        <circle cx="9" cy="9" r="8" fill="none" stroke="currentColor" strokeWidth="1.6" />
        <path d="M9 5v5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <circle cx="9" cy="12.8" r="1" fill="currentColor" />
      </svg>
      <div>
        <p className="error-notice__title">{title}</p>
        {detail && <p className="error-notice__detail">{detail}</p>}
        {action && <div style={{ marginTop: 'var(--space-3)' }}>{action}</div>}
      </div>
    </div>
  )
}

/* -- Selo --------------------------------------------------------------------- */

type BadgeTone = 'neutral' | 'positive' | 'negative' | 'info' | 'warning'

export function Badge({
  tone = 'neutral',
  children,
}: {
  tone?: BadgeTone
  children: ReactNode
}) {
  return <span className={cx('badge', `badge--${tone}`)}>{children}</span>
}

/* -- Progresso ----------------------------------------------------------------- */

interface ProgressProps {
  /** De 0 a 100. Valores acima são achatados para a barra não vazar. */
  value: number
  color?: string
  size?: 'sm' | 'md' | 'lg'
  label?: string
}

export function Progress({ value, color, size = 'md', label }: ProgressProps) {
  const clamped = Math.max(0, Math.min(100, value))
  return (
    <div
      className={cx('progress', size !== 'md' && `progress--${size}`)}
      role="progressbar"
      aria-valuenow={Math.round(clamped)}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
    >
      <div
        className="progress__fill"
        style={{ width: `${clamped}%`, backgroundColor: color }}
      />
    </div>
  )
}
