/**
 * Utilitários de cor para superfícies pintadas pelo usuário.
 *
 * O usuário escolhe qualquer cor para o cartão, então o texto por cima não pode
 * ser sempre branco: sobre um amarelo claro ele some. Aqui decidimos a tinta a
 * partir da luminância real da cor.
 */

interface Rgb {
  r: number
  g: number
  b: number
}

/** Aceita #RGB, #RRGGBB e #RRGGBBAA. Devolve null se não reconhecer. */
export function parseHex(color: string): Rgb | null {
  const hex = color.trim().replace('#', '')

  if (hex.length === 3) {
    const [r, g, b] = hex
    if (!r || !g || !b) return null
    return {
      r: parseInt(r + r, 16),
      g: parseInt(g + g, 16),
      b: parseInt(b + b, 16),
    }
  }

  if (hex.length === 6 || hex.length === 8) {
    const value = hex.slice(0, 6)
    if (!/^[0-9a-fA-F]{6}$/.test(value)) return null
    return {
      r: parseInt(value.slice(0, 2), 16),
      g: parseInt(value.slice(2, 4), 16),
      b: parseInt(value.slice(4, 6), 16),
    }
  }

  return null
}

/**
 * Luminância relativa segundo a WCAG: 0 = preto, 1 = branco.
 *
 * Os coeficientes não são iguais porque o olho humano é muito mais sensível ao
 * verde que ao azul — por isso um azul escuro e um verde de mesma "intensidade"
 * pedem tintas diferentes.
 */
export function relativeLuminance(color: string): number {
  const rgb = parseHex(color)
  if (!rgb) return 0

  const channel = (value: number): number => {
    const normalized = value / 255
    return normalized <= 0.03928
      ? normalized / 12.92
      : ((normalized + 0.055) / 1.055) ** 2.4
  }

  return 0.2126 * channel(rgb.r) + 0.7152 * channel(rgb.g) + 0.0722 * channel(rgb.b)
}

/**
 * Tinta legível sobre a cor de fundo informada.
 *
 * O corte em 0,45 (e não 0,5) puxa para o branco: cartão é objeto escuro por
 * convenção, e branco sobre um tom médio lê melhor que cinza-escuro.
 */
export function readableInk(background: string): string {
  return relativeLuminance(background) > 0.45 ? '#1C1C1E' : '#FFFFFF'
}

/** Clareia (amount > 0) ou escurece (amount < 0) uma cor. `amount` de -1 a 1. */
export function shade(color: string, amount: number): string {
  const rgb = parseHex(color)
  if (!rgb) return color

  const apply = (value: number): number => {
    const target = amount > 0 ? 255 : 0
    return Math.round(value + (target - value) * Math.abs(amount))
  }

  const toHex = (value: number) => value.toString(16).padStart(2, '0')
  return `#${toHex(apply(rgb.r))}${toHex(apply(rgb.g))}${toHex(apply(rgb.b))}`
}

/** `rgba()` a partir de um hex, para véus e brilhos sobre a cor do cartão. */
export function withAlpha(color: string, alpha: number): string {
  const rgb = parseHex(color)
  if (!rgb) return color
  return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`
}
