import type { SVGProps } from 'react'

/**
 * Ícones desenhados em traço fino e uniforme (1.6), sem preenchimento.
 *
 * São inline de propósito: uma biblioteca de ícones traria milhares que não
 * usamos, e o traço único é o que mantém a interface coesa.
 */

export type IconName =
  | 'dashboard'
  | 'wallet'
  | 'card'
  | 'transactions'
  | 'tag'
  | 'repeat'
  | 'budget'
  | 'target'
  | 'installments'
  | 'trending-up'
  | 'reports'
  | 'settings'
  | 'plus'
  | 'search'
  | 'filter'
  | 'chevron-right'
  | 'chevron-left'
  | 'chevron-down'
  | 'arrow-up'
  | 'arrow-down'
  | 'arrow-swap'
  | 'edit'
  | 'trash'
  | 'logout'
  | 'menu'
  | 'close'
  | 'check'
  | 'calendar'
  | 'bank'
  | 'home'
  | 'utensils'
  | 'car'
  | 'heart'
  | 'book'
  | 'sparkles'
  | 'bag'
  | 'plane'
  | 'ellipsis'
  | 'sun'
  | 'moon'
  | 'alert'

const PATHS: Record<IconName, string> = {
  dashboard: 'M3 9.5 12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1V9.5Z',
  wallet: 'M3 8a2 2 0 0 1 2-2h13a1 1 0 0 1 1 1v2M3 8v9a2 2 0 0 0 2 2h14a1 1 0 0 0 1-1v-3M3 8h16M21 11h-4a2 2 0 0 0 0 4h4v-4Z',
  card: 'M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7ZM3 10h18M7 15h3',
  transactions: 'M4 7h13l-3-3M20 17H7l3 3',
  tag: 'M3 11.5V4a1 1 0 0 1 1-1h7.5a1 1 0 0 1 .7.3l8.5 8.5a1 1 0 0 1 0 1.4l-7.5 7.5a1 1 0 0 1-1.4 0l-8.5-8.5a1 1 0 0 1-.3-.7ZM7.5 7.5h.01',
  repeat: 'M4 9V7a2 2 0 0 1 2-2h11l-3-3M20 15v2a2 2 0 0 1-2 2H7l3 3',
  budget: 'M4 20V10M10 20V4M16 20v-7M22 20H2',
  target: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM12 16.5a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9ZM12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z',
  installments: 'M3 6a2 2 0 0 1 2-2h11a2 2 0 0 1 2 2M5 9h14a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2ZM8 15h8',
  'trending-up': 'M3 17l6-6 4 4 8-8M21 7v5m0-5h-5',
  reports: 'M4 4v16h16M8 16V10M12.5 16V6M17 16v-4',
  settings: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM19.4 14.5a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.6 1.6 0 0 0-1-1.5 1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.6 1.6 0 0 0 1.5-1 1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H9a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1Z',
  plus: 'M12 5v14M5 12h14',
  search: 'M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14ZM20 20l-4-4',
  filter: 'M3 5h18l-7 8v6l-4 2v-8L3 5Z',
  'chevron-right': 'M9 5l7 7-7 7',
  'chevron-left': 'M15 5l-7 7 7 7',
  'chevron-down': 'M5 9l7 7 7-7',
  'arrow-up': 'M12 20V4M5 11l7-7 7 7',
  'arrow-down': 'M12 4v16M5 13l7 7 7-7',
  'arrow-swap': 'M7 4v16M7 20l-3-3M17 20V4M17 4l3 3',
  edit: 'M4 20h4l10.5-10.5a2.1 2.1 0 0 0-3-3L5 17v3ZM14.5 6.5l3 3',
  trash: 'M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2M6 7l1 13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1l1-13M10 11v6M14 11v6',
  logout: 'M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 17l-5-5 5-5M5 12h11',
  menu: 'M4 7h16M4 12h16M4 17h16',
  close: 'M6 6l12 12M18 6L6 18',
  check: 'M4 12.5l5 5L20 6.5',
  calendar: 'M5 5h14a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1ZM4 10h16M8 3v4M16 3v4',
  bank: 'M3 10h18M3 10 12 4l9 6M5 10v8M10 10v8M14 10v8M19 10v8M3 21h18',
  home: 'M3 10 12 3l9 7v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V10Z',
  utensils: 'M6 3v8a2 2 0 0 0 4 0V3M8 11v10M17 3c-1.5 1-2 3-2 5s.5 3 2 3v10',
  car: 'M5 17h14M4 17v-4l2-5h12l2 5v4M4 17v2h3v-2M17 17v2h3v-2M7.5 13h.01M16.5 13h.01',
  heart: 'M12 20s-7-4.5-7-9.5A4 4 0 0 1 12 8a4 4 0 0 1 7-2.5C19 15.5 12 20 12 20Z',
  book: 'M5 4h11a2 2 0 0 1 2 2v14H7a2 2 0 0 1-2-2V4ZM5 17h13',
  sparkles: 'M12 3l1.8 4.7L18.5 9.5 13.8 11.3 12 16l-1.8-4.7L5.5 9.5l4.7-1.8L12 3ZM18.5 15l.9 2.2 2.1.8-2.1.9-.9 2.1-.9-2.1-2.1-.9 2.1-.8.9-2.2Z',
  bag: 'M6 8h12l1 12H5L6 8ZM9 8V6a3 3 0 0 1 6 0v2',
  plane: 'M10.5 3.5a1.5 1.5 0 0 1 3 0V9l7 4v2l-7-2v4l2 1.5V20l-3.5-1L8.5 20v-1.5L10.5 17v-4l-7 2v-2l7-4V3.5Z',
  ellipsis: 'M6 12h.01M12 12h.01M18 12h.01',
  sun: 'M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10ZM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4',
  moon: 'M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z',
  alert: 'M12 3 2 20h20L12 3ZM12 10v4M12 17.5h.01',
}

interface IconProps extends Omit<SVGProps<SVGSVGElement>, 'name'> {
  name: IconName
  size?: number
}

export function Icon({ name, size = 20, ...rest }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      {...rest}
    >
      <path d={PATHS[name]} />
    </svg>
  )
}

/** Resolve o nome guardado em contas e categorias, com fallback seguro. */
export function iconOf(name: string | null | undefined, fallback: IconName = 'tag'): IconName {
  return name && name in PATHS ? (name as IconName) : fallback
}
