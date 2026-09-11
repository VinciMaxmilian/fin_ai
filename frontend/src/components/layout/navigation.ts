import type { IconName } from '@/components/ui/Icon'

export interface NavItem {
  label: string
  path: string
  icon: IconName
}

export interface NavGroup {
  /** Sem título, o grupo aparece solto no topo — é o caso do Dashboard. */
  title?: string
  items: NavItem[]
}

/** Fonte única da navegação: sidebar, menu mobile e breadcrumbs leem daqui. */
export const NAVIGATION: NavGroup[] = [
  {
    items: [{ label: 'Dashboard', path: '/', icon: 'dashboard' }],
  },
  {
    title: 'Finanças',
    items: [
      { label: 'Contas', path: '/contas', icon: 'wallet' },
      { label: 'Cartões', path: '/cartoes', icon: 'card' },
      { label: 'Transações', path: '/transacoes', icon: 'transactions' },
      { label: 'Categorias', path: '/categorias', icon: 'tag' },
      { label: 'Contas recorrentes', path: '/recorrentes', icon: 'repeat' },
    ],
  },
  {
    title: 'Planejamento',
    items: [
      { label: 'Orçamento', path: '/orcamento', icon: 'budget' },
      { label: 'Metas', path: '/metas', icon: 'target' },
      { label: 'Parcelamentos', path: '/parcelamentos', icon: 'installments' },
    ],
  },
  {
    title: 'Patrimônio',
    items: [
      { label: 'Investimentos', path: '/investimentos', icon: 'trending-up' },
      { label: 'Patrimônio', path: '/patrimonio', icon: 'bank' },
    ],
  },
  {
    items: [
      { label: 'Relatórios', path: '/relatorios', icon: 'reports' },
      { label: 'Configurações', path: '/configuracoes', icon: 'settings' },
    ],
  },
]

/**
 * No celular a barra inferior comporta cinco destinos. Os outros ficam atrás
 * de "Mais", em vez de espremer a interface de desktop na tela pequena.
 */
export const BOTTOM_NAV: NavItem[] = [
  { label: 'Início', path: '/', icon: 'dashboard' },
  { label: 'Transações', path: '/transacoes', icon: 'transactions' },
  { label: 'Cartões', path: '/cartoes', icon: 'card' },
  { label: 'Orçamento', path: '/orcamento', icon: 'budget' },
]

export function findNavItem(pathname: string): NavItem | undefined {
  const all = NAVIGATION.flatMap((group) => group.items)
  // Rota mais específica primeiro, para /contas não capturar /contas/123.
  return (
    all.find((item) => item.path === pathname) ??
    all.filter((item) => item.path !== '/').find((item) => pathname.startsWith(item.path))
  )
}
