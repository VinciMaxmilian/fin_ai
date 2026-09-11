import type { ElementType, HTMLAttributes, ReactNode } from 'react'
import { cx } from '@/utils/cx'
import './glass.css'

export type GlassLevel = 1 | 2 | 3

interface GlassSurfaceProps extends HTMLAttributes<HTMLDivElement> {
  /** Profundidade aparente da superfície. Quanto maior, mais opaca e elevada. */
  level?: GlassLevel
  children?: ReactNode
}

/**
 * Superfície de vidro crua, sem espaçamento próprio.
 * Serve de base para os componentes abaixo e para casos avulsos.
 */
export function GlassSurface({ level = 2, className, children, ...rest }: GlassSurfaceProps) {
  return (
    <div className={cx('glass', `glass--level-${level}`, className)} {...rest}>
      {children}
    </div>
  )
}

// `title` do HTML é string; aqui aceita qualquer nó, então substituímos.
interface GlassCardProps extends Omit<GlassSurfaceProps, 'title'> {
  title?: ReactNode
  subtitle?: ReactNode
  /** Conteúdo alinhado à direita do cabeçalho: ações, filtros, um valor. */
  action?: ReactNode
  compact?: boolean
  /** Remove o espaçamento interno — para listas e tabelas que vão até a borda. */
  flush?: boolean
  as?: ElementType
}

export function GlassCard({
  title,
  subtitle,
  action,
  compact = false,
  flush = false,
  level = 2,
  className,
  children,
  as: Tag = 'section',
  ...rest
}: GlassCardProps) {
  const hasHeader = Boolean(title || subtitle || action)

  return (
    <Tag
      className={cx(
        'glass',
        `glass--level-${level}`,
        'glass-card',
        compact && 'glass-card--compact',
        flush && 'glass-card--flush',
        className,
      )}
      {...rest}
    >
      {hasHeader && (
        <header className="glass-card__header">
          <div>
            {title && <h2 className="glass-card__title">{title}</h2>}
            {subtitle && <p className="glass-card__subtitle">{subtitle}</p>}
          </div>
          {action}
        </header>
      )}
      {children}
    </Tag>
  )
}

export function GlassPanel({ level = 1, className, children, ...rest }: GlassSurfaceProps) {
  return (
    <div
      className={cx('glass', `glass--level-${level}`, 'glass-panel', className)}
      {...rest}
    >
      {children}
    </div>
  )
}
