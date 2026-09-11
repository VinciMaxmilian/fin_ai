import { useId } from 'react'
import type { CardBrand } from '@/types/api'

/**
 * Marcas das bandeiras, desenhadas em SVG.
 *
 * São representações simplificadas, feitas para identificar o cartão do próprio
 * usuário na interface dele — não reproduções dos logos oficiais. Mantê-las
 * geométricas e no mesmo peso visual é o que faz a lista parecer um conjunto, e
 * não uma colagem de arquivos de marcas diferentes.
 *
 * `ink` é a cor do texto legível sobre o cartão, calculada a partir da cor
 * escolhida (ver `utils/color.ts`). As bandeiras que têm cor própria e
 * reconhecível — Mastercard — a mantêm; as que são só tipografia usam a tinta.
 */

interface BrandMarkProps {
  brand: CardBrand
  /** Cor legível sobre o fundo do cartão. */
  ink: string
  height?: number
}

export function BrandMark({ brand, ink, height = 22 }: BrandMarkProps) {
  // Id único por instância: dois cartões Mastercard na mesma tela
  // duplicariam o id do recorte, e o SVG usaria sempre o primeiro.
  const clipId = useId()

  switch (brand) {
    case 'mastercard':
      // Dois círculos sobrepostos: a única bandeira aqui reconhecida pela
      // forma, então vale manter as cores originais.
      return (
        <svg height={height} viewBox="0 0 48 30" fill="none" aria-label="Mastercard">
          <defs>
            {/* A lente da sobreposição é a interseção dos dois círculos: sai
                mais fiel de um recorte que de um path desenhado à mão. */}
            <clipPath id={clipId}>
              <circle cx="17" cy="15" r="13" />
            </clipPath>
          </defs>
          <circle cx="17" cy="15" r="13" fill="#EB001B" />
          <circle cx="31" cy="15" r="13" fill="#F79E1B" />
          <circle cx="31" cy="15" r="13" fill="#FF5F00" clipPath={`url(#${clipId})`} />
        </svg>
      )

    case 'visa':
      return (
        <svg height={height} viewBox="0 0 52 20" aria-label="Visa">
          <text
            x="0"
            y="16"
            fill={ink}
            fontFamily="-apple-system, 'Segoe UI', Arial, sans-serif"
            fontSize="19"
            fontWeight="700"
            fontStyle="italic"
            letterSpacing="1.5"
          >
            VISA
          </text>
        </svg>
      )

    case 'elo':
      return (
        <svg height={height} viewBox="0 0 46 24" fill="none" aria-label="Elo">
          <circle cx="12" cy="12" r="10" fill={ink} opacity="0.18" />
          <path d="M12 2a10 10 0 0 1 9.3 6.3l-4 1.6A5.7 5.7 0 0 0 12 6.3Z" fill="#FFCB05" />
          <path d="M21.3 15.7A10 10 0 0 1 12 22v-4.3a5.7 5.7 0 0 0 5.3-3.6Z" fill="#00A4E0" />
          <path d="M12 2v4.3a5.7 5.7 0 0 0-5.3 3.6l-4-1.6A10 10 0 0 1 12 2Z" fill="#EF4123" />
          <text
            x="25"
            y="17"
            fill={ink}
            fontFamily="-apple-system, 'Segoe UI', Arial, sans-serif"
            fontSize="13"
            fontWeight="600"
          >
            elo
          </text>
        </svg>
      )

    case 'amex':
      return (
        <svg height={height} viewBox="0 0 42 24" fill="none" aria-label="American Express">
          {/* Azul fixo da bandeira: usar a tinta do cartão deixava a caixa
              escura com texto azul em cartões claros, ilegível. */}
          <rect width="42" height="24" rx="3" fill="#006FCF" />
          <text
            x="21"
            y="15.5"
            textAnchor="middle"
            fill="#FFFFFF"
            fontFamily="-apple-system, 'Segoe UI', Arial, sans-serif"
            fontSize="9"
            fontWeight="700"
            letterSpacing="0.4"
          >
            AMEX
          </text>
        </svg>
      )

    case 'hipercard':
      return (
        <svg height={height} viewBox="0 0 74 20" aria-label="Hipercard">
          <text
            x="0"
            y="15"
            fill={ink}
            fontFamily="-apple-system, 'Segoe UI', Arial, sans-serif"
            fontSize="14"
            fontWeight="700"
            letterSpacing="-0.3"
          >
            Hipercard
          </text>
        </svg>
      )

    default:
      // Sem bandeira definida: o símbolo de aproximação, que é neutro e
      // continua dizendo "isto é um cartão".
      return (
        <svg height={height} viewBox="0 0 24 24" fill="none" aria-label="Cartão">
          <path
            d="M8.5 7.5a7 7 0 0 1 0 9M12 5a10.5 10.5 0 0 1 0 14M15.5 2.5a14 14 0 0 1 0 19"
            stroke={ink}
            strokeWidth="1.8"
            strokeLinecap="round"
            opacity="0.85"
          />
        </svg>
      )
  }
}
