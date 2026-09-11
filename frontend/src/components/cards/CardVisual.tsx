import { BrandMark } from './BrandMark'
import { readableInk, shade, withAlpha } from '@/utils/color'
import { cx } from '@/utils/cx'
import type { CardBrand } from '@/types/api'
import './card-visual.css'

interface CardVisualProps {
  name: string
  brand: CardBrand
  /** Cor escolhida pelo usuário. Define o degradê e a tinta do texto. */
  color: string
  bank?: string | null
  size?: 'sm' | 'md'
  /** Cartão arquivado fica dessaturado, sem sumir da lista. */
  muted?: boolean
}

/**
 * Miniatura do cartão de crédito.
 *
 * Existe para o reconhecimento ser instantâneo: numa lista de cinco cartões, a
 * cor e a bandeira identificam o certo antes de você ler o nome.
 *
 * O degradê é derivado da cor escolhida — clareia no topo e escurece na base,
 * imitando luz caindo sobre um plástico. A tinta do texto é calculada pela
 * luminância, então funciona tanto num roxo escuro quanto num amarelo claro.
 */
export function CardVisual({
  name,
  brand,
  color,
  bank,
  size = 'md',
  muted = false,
}: CardVisualProps) {
  const ink = readableInk(color)
  const isLight = ink !== '#FFFFFF'

  return (
    <div
      className={cx('card-visual', `card-visual--${size}`, muted && 'card-visual--muted')}
      style={{
        // Degradê diagonal: claro no canto superior esquerdo, escuro no inferior
        // direito, como o plástico reflete a luz.
        backgroundImage: `linear-gradient(145deg, ${shade(color, 0.2)} 0%, ${color} 46%, ${shade(color, -0.22)} 100%)`,
        color: ink,
      }}
      aria-hidden="true"
    >
      {/* Reflexo diagonal, bem discreto. */}
      <span
        className="card-visual__sheen"
        style={{
          backgroundImage: `linear-gradient(118deg, ${withAlpha(
            isLight ? '#000000' : '#FFFFFF',
            isLight ? 0.05 : 0.16,
          )} 0%, transparent 42%)`,
        }}
      />

      <div className="card-visual__top">
        <Chip ink={ink} />
        <BrandMark brand={brand} ink={ink} height={size === 'sm' ? 16 : 21} />
      </div>

      <div className="card-visual__bottom">
        <span className="card-visual__name">{name}</span>
        {bank && size !== 'sm' && <span className="card-visual__bank">{bank}</span>}
      </div>
    </div>
  )
}

/** Chip dourado estilizado: é o que faz o retângulo virar "cartão" no olhar. */
function Chip({ ink }: { ink: string }) {
  const isLight = ink !== '#FFFFFF'
  return (
    <svg
      className="card-visual__chip"
      viewBox="0 0 32 24"
      fill="none"
      aria-hidden="true"
    >
      <rect
        width="32"
        height="24"
        rx="4"
        fill={isLight ? 'rgba(0,0,0,0.16)' : 'rgba(255,255,255,0.34)'}
      />
      <path
        d="M0 8h32M0 16h32M11 0v24M21 0v24"
        stroke={isLight ? 'rgba(0,0,0,0.2)' : 'rgba(255,255,255,0.38)'}
        strokeWidth="1.4"
      />
      <rect
        x="10"
        y="7"
        width="12"
        height="10"
        rx="2"
        fill={isLight ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.26)'}
      />
    </svg>
  )
}
