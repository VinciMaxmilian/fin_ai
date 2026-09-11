import { Navigate, Route, Routes } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { useAuth } from '@/stores/auth'
import { useTheme } from '@/hooks/useTheme'
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { AccountsPage } from '@/pages/AccountsPage'
import { CardsPage } from '@/pages/CardsPage'
import { TransactionsPage } from '@/pages/TransactionsPage'
import { CategoriesPage } from '@/pages/CategoriesPage'
import { RecurringPage } from '@/pages/RecurringPage'
import { BudgetPage } from '@/pages/BudgetPage'
import { GoalsPage } from '@/pages/GoalsPage'
import { InstallmentsPage } from '@/pages/InstallmentsPage'
import { InvestmentsPage } from '@/pages/InvestmentsPage'
import { NetWorthPage } from '@/pages/NetWorthPage'
import { ReportsPage } from '@/pages/ReportsPage'
import { SettingsPage } from '@/pages/SettingsPage'

export function App() {
  const { session, loading } = useAuth()
  // Aplica o tema salvo já na primeira renderização.
  useTheme()

  if (loading && !session) {
    return <BootScreen />
  }

  if (!session) {
    return (
      <Routes>
        <Route path="/entrar" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/entrar" replace />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route path="/entrar" element={<Navigate to="/" replace />} />
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="contas" element={<AccountsPage />} />
        <Route path="cartoes" element={<CardsPage />} />
        <Route path="transacoes" element={<TransactionsPage />} />
        <Route path="categorias" element={<CategoriesPage />} />
        <Route path="recorrentes" element={<RecurringPage />} />
        <Route path="orcamento" element={<BudgetPage />} />
        <Route path="metas" element={<GoalsPage />} />
        <Route path="parcelamentos" element={<InstallmentsPage />} />
        <Route path="investimentos" element={<InvestmentsPage />} />
        <Route path="patrimonio" element={<NetWorthPage />} />
        <Route path="relatorios" element={<ReportsPage />} />
        <Route path="configuracoes" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

/** Tela mínima enquanto a sessão é restaurada, para não piscar o login. */
function BootScreen() {
  return (
    <div
      style={{
        minHeight: '100dvh',
        display: 'grid',
        placeItems: 'center',
        color: 'var(--text-tertiary)',
        fontSize: 'var(--text-sm)',
      }}
    >
      Carregando…
    </div>
  )
}
