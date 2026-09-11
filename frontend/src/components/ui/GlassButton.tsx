import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cx } from '@/utils/cx'
import './glass.css'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

interface GlassButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  /** Ocupa toda a largura disponível. */
  block?: boolean
  /** Só ícone: deixa o botão quadrado. Exige `aria-label`. */
  iconOnly?: boolean
  loading?: boolean
  children?: ReactNode
}

export function GlassButton({
  variant = 'secondary',
  size = 'md',
  block = false,
  iconOnly = false,
  loading = false,
  disabled,
  className,
  children,
  ...rest
}: GlassButtonProps) {
  return (
    <button
      className={cx(
        'glass-button',
        `glass-button--${variant}`,
        size !== 'md' && `glass-button--${size}`,
        block && 'glass-button--block',
        iconOnly && 'glass-button--icon',
        className,
      )}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...rest}
    >
      {loading ? <Spinner /> : children}
    </button>
  )
}

function Spinner() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
      <circle
        cx="8"
        cy="8"
        r="6.5"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeDasharray="30 12"
        opacity="0.9"
      >
        <animateTransform
          attributeName="transform"
          type="rotate"
          from="0 8 8"
          to="360 8 8"
          dur="0.7s"
          repeatCount="indefinite"
        />
      </circle>
    </svg>
  )
}
