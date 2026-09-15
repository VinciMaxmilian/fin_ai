import { NavLink } from 'react-router-dom'
import { APP_NAME, APP_SYMBOL } from '@/brand'
import { Icon } from '@/components/ui/Icon'
import { ProjectCredit } from '@/components/ui/ProjectCredit'
import { NAVIGATION } from './navigation'
import { useAuth } from '@/stores/auth'
import { cx } from '@/utils/cx'
import './layout.css'

/** Marca do app. Compartilhada entre sidebar, gaveta e tela de login. */
export function Brand({ showWordmark = true }: { showWordmark?: boolean }) {
  return (
    <div className="sidebar__brand">
      <span className="sidebar__logo" aria-hidden="true">
        {APP_SYMBOL}
      </span>
      {showWordmark && <span className="sidebar__wordmark">{APP_NAME}</span>}
    </div>
  )
}

export function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="sidebar__nav" aria-label="Navegação principal">
      {NAVIGATION.map((group, index) => (
        <div key={group.title ?? `grupo-${index}`}>
          {group.title && <p className="nav-group__title">{group.title}</p>}
          <ul className="nav-group__items">
            {group.items.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  end={item.path === '/'}
                  onClick={onNavigate}
                  className={({ isActive }) => cx('nav-link', isActive && 'nav-link--active')}
                  title={item.label}
                >
                  <Icon name={item.icon} size={19} className="nav-link__icon" />
                  <span>{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  )
}

export function UserChip({ onClick }: { onClick?: () => void }) {
  const { profile } = useAuth()
  const name = profile?.full_name ?? profile?.email ?? ''
  const initial = name.charAt(0).toUpperCase() || '?'

  return (
    <button type="button" className="user-chip" onClick={onClick}>
      <span className="user-chip__avatar">
        {profile?.avatar_url ? (
          <img src={profile.avatar_url} alt="" />
        ) : (
          <span aria-hidden="true">{initial}</span>
        )}
      </span>
      <span className="user-chip__info">
        <span className="user-chip__name">{profile?.full_name ?? 'Minha conta'}</span>
        <span className="user-chip__email">{profile?.email}</span>
      </span>
    </button>
  )
}

export function Sidebar() {
  const { signOut } = useAuth()

  return (
    <aside className="sidebar">
      <Brand />
      <NavLinks />
      <div className="sidebar__footer">
        <ProjectCredit variant="sidebar" />
        <UserChip />
        <button type="button" className="nav-link" onClick={() => void signOut()}>
          <Icon name="logout" size={19} className="nav-link__icon" />
          <span>Sair</span>
        </button>
      </div>
    </aside>
  )
}
