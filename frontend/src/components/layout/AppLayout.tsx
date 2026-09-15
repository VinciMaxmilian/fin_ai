import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { APP_NAME } from '@/brand'
import { Icon } from '@/components/ui/Icon'
import { GlassButton } from '@/components/ui/GlassButton'
import { ProjectCredit } from '@/components/ui/ProjectCredit'
import { SecurityNotice } from '@/components/ui/SecurityNotice'
import { Brand, NavLinks, Sidebar, UserChip } from './Sidebar'
import { BOTTOM_NAV, findNavItem } from './navigation'
import { useAuth } from '@/stores/auth'
import { useTheme } from '@/hooks/useTheme'
import { cx } from '@/utils/cx'
import './layout.css'

export function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { signOut } = useAuth()
  const { theme, toggle } = useTheme()
  const [drawerOpen, setDrawerOpen] = useState(false)

  const current = findNavItem(location.pathname)
  const title = current?.label ?? APP_NAME

  // Mudou de rota: a gaveta fecha sozinha.
  useEffect(() => {
    setDrawerOpen(false)
  }, [location.pathname])

  useEffect(() => {
    document.title = title === APP_NAME ? APP_NAME : `${title} · ${APP_NAME}`
  }, [title])

  return (
    <div className="app-shell">
      <Sidebar />

      <div className="app-main">
        <header className="topbar">
          <div className="row" style={{ gap: 'var(--space-3)', minWidth: 0 }}>
            <GlassButton
              variant="ghost"
              size="sm"
              iconOnly
              aria-label="Abrir menu"
              onClick={() => setDrawerOpen(true)}
              className="topbar__mobile-brand"
            >
              <Icon name="menu" size={20} />
            </GlassButton>
            <h1 className="topbar__title">{title}</h1>
          </div>

          <div className="topbar__actions">
            <GlassButton
              variant="ghost"
              size="sm"
              iconOnly
              onClick={toggle}
              aria-label={theme === 'dark' ? 'Usar tema claro' : 'Usar tema escuro'}
            >
              <Icon name={theme === 'dark' ? 'sun' : 'moon'} size={18} />
            </GlassButton>
            <GlassButton
              variant="primary"
              size="sm"
              onClick={() => navigate('/transacoes?novo=1')}
            >
              <Icon name="plus" size={16} />
              <span>Lançamento</span>
            </GlassButton>
          </div>
        </header>

        <main className="app-content">
          <Outlet />
          <SecurityNotice variant="footer" />
        </main>
      </div>

      {drawerOpen && (
        <>
          <div className="drawer__backdrop" onClick={() => setDrawerOpen(false)} />
          <div className="drawer" role="dialog" aria-label="Menu de navegação">
            <Brand />
            <NavLinks onNavigate={() => setDrawerOpen(false)} />
            <div className="sidebar__footer">
              <ProjectCredit variant="sidebar" />
              <UserChip onClick={() => navigate('/configuracoes')} />
              <button type="button" className="nav-link" onClick={() => void signOut()}>
                <Icon name="logout" size={19} className="nav-link__icon" />
                <span>Sair</span>
              </button>
            </div>
          </div>
        </>
      )}

      <nav className="bottom-nav" aria-label="Navegação">
        <ul className="bottom-nav__list">
          {BOTTOM_NAV.slice(0, 2).map((item) => (
            <BottomLink key={item.path} {...item} />
          ))}

          <li style={{ display: 'grid', placeItems: 'center' }}>
            <button
              type="button"
              className="bottom-nav__fab"
              aria-label="Novo lançamento"
              onClick={() => navigate('/transacoes?novo=1')}
            >
              <Icon name="plus" size={22} />
            </button>
          </li>

          {BOTTOM_NAV.slice(2).map((item) => (
            <BottomLink key={item.path} {...item} />
          ))}
        </ul>
      </nav>
    </div>
  )
}

function BottomLink({ label, path, icon }: (typeof BOTTOM_NAV)[number]) {
  return (
    <li>
      <NavLink
        to={path}
        end={path === '/'}
        className={({ isActive }) =>
          cx('bottom-nav__link', isActive && 'bottom-nav__link--active')
        }
      >
        <Icon name={icon} size={21} />
        <span>{label}</span>
      </NavLink>
    </li>
  )
}
