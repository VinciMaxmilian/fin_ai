/**
 * Paleta categórica dos gráficos.
 *
 * As oito matizes abaixo foram verificadas com o validador de paletas nos dois
 * temas. Resultado registrado:
 *
 *   claro  — separação para daltonismo: pior par adjacente ΔE 9.1 (protanopia);
 *            visão normal ΔE 19.6; três matizes ficam abaixo de 3:1 de
 *            contraste sobre a superfície clara.
 *   escuro — separação ΔE 8.4; visão normal ΔE 19.3; todas acima de 3:1.
 *
 * O contraste baixo no tema claro é compensado como manda a regra: **todo
 * gráfico de categoria é uma lista de barras ordenada, com nome e valor
 * escritos em cada linha**. A cor reforça a identidade, nunca a carrega
 * sozinha. Nenhum gráfico do app depende de distinguir matizes para ser lido.
 *
 * Não acrescente uma nona cor: o espaço de matizes com croma suficiente acaba
 * aqui, e a nona sempre cai abaixo do piso e vira cinza. Acima de oito séries,
 * o excedente é agrupado em "Outros" — que é o que o backend já faz.
 */

export interface PaletteSlot {
  light: string
  dark: string
}

export const CATEGORICAL: PaletteSlot[] = [
  { light: '#2A78D6', dark: '#3987E5' }, // azul
  { light: '#EB6834', dark: '#D95926' }, // laranja
  { light: '#1BAF7A', dark: '#199E70' }, // água
  { light: '#EDA100', dark: '#C98500' }, // amarelo
  { light: '#E87BA4', dark: '#D55181' }, // magenta
  { light: '#008300', dark: '#008300' }, // verde
  { light: '#4A3AA7', dark: '#9085E9' }, // violeta
  { light: '#E34948', dark: '#E66767' }, // vermelho
]

/** Cinza do agrupamento "Outros". Fora da rotação categórica de propósito. */
export const MUTED_SLOT: PaletteSlot = { light: '#898781', dark: '#898781' }

const DARK_BY_LIGHT = new Map<string, string>(
  [...CATEGORICAL, MUTED_SLOT].map((slot) => [slot.light.toUpperCase(), slot.dark]),
)

/**
 * Converte uma cor guardada no banco para a versão do tema atual.
 *
 * Cores fora da paleta (criadas pelo usuário) passam intactas — é a escolha
 * dele, e o rótulo direto ao lado garante a leitura.
 */
export function themedColor(color: string, theme: 'light' | 'dark'): string {
  if (theme === 'light') return color
  return DARK_BY_LIGHT.get(color.toUpperCase()) ?? color
}

/** Cores semânticas dos gráficos. Lidas dos tokens para acompanhar o tema. */
export const SEMANTIC = {
  income: 'var(--positive)',
  expense: 'var(--negative)',
  balance: 'var(--accent)',
  neutral: 'var(--text-tertiary)',
} as const
