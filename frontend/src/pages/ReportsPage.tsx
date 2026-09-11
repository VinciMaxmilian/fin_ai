import { useState } from 'react'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { EmptyState, ErrorNotice, Skeleton } from '@/components/ui/Feedback'
import { Icon } from '@/components/ui/Icon'
import { GroupedBars } from '@/components/charts/GroupedBars'
import { BarList } from '@/components/charts/BarList'
import { TrendChart } from '@/components/charts/TrendChart'
import { SEMANTIC } from '@/components/charts/palette'
import { useAsync } from '@/hooks/useAsync'
import { reportsApi } from '@/services/endpoints'
import {
  addMonths,
  firstDayOfMonth,
  formatMoney,
  formatMonth,
  formatMonthShort,
  toNumber,
} from '@/utils/format'
import '@/components/ui/page.css'
import '@/components/charts/charts.css'

export function ReportsPage() {
  const [month, setMonth] = useState(firstDayOfMonth())
  const monthEnd = addMonths(month, 1)

  const monthly = useAsync(() => reportsApi.monthly(12), [])
  const byCategory = useAsync(
    () => reportsApi.expensesByCategory(month, lastDayOf(month)),
    [month],
  )
  const byCard = useAsync(() => reportsApi.cardSpending(month, lastDayOf(month)), [month])
  const recurring = useAsync(() => reportsApi.recurring(), [])
  const netWorth = useAsync(() => reportsApi.netWorth(12), [])

  const [showTable, setShowTable] = useState(false)
  const points = monthly.data?.points ?? []

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">Relatórios</h2>
          <p className="page__lede">Os mesmos números, vistos de outros ângulos.</p>
        </div>
        <div className="row" style={{ gap: 'var(--space-2)' }}>
          <GlassButton
            size="sm"
            iconOnly
            aria-label="Mês anterior"
            onClick={() => setMonth(addMonths(month, -1))}
          >
            <Icon name="chevron-left" size={15} />
          </GlassButton>
          <span
            style={{
              minWidth: 152,
              textAlign: 'center',
              fontWeight: 'var(--weight-medium)',
              textTransform: 'capitalize',
            }}
          >
            {formatMonth(month)}
          </span>
          <GlassButton
            size="sm"
            iconOnly
            aria-label="Próximo mês"
            disabled={monthEnd > firstDayOfMonth(new Date())}
            onClick={() => setMonth(addMonths(month, 1))}
          >
            <Icon name="chevron-right" size={15} />
          </GlassButton>
        </div>
      </div>

      {monthly.error && <ErrorNotice detail={monthly.error} />}

      <GlassCard
        title="Receitas x despesas"
        subtitle="Últimos 12 meses"
        action={
          <button
            type="button"
            className="chart-table-toggle"
            onClick={() => setShowTable((value) => !value)}
          >
            {showTable ? 'Ver gráfico' : 'Ver tabela'}
          </button>
        }
      >
        {monthly.loading ? (
          <Skeleton height={260} radius="var(--radius-md)" />
        ) : showTable ? (
          <div style={{ overflowX: 'auto' }}>
            <table className="chart-table">
              <thead>
                <tr>
                  <th scope="col">Mês</th>
                  <th scope="col">Receitas</th>
                  <th scope="col">Despesas</th>
                  <th scope="col">Saldo</th>
                </tr>
              </thead>
              <tbody>
                {points.map((point) => (
                  <tr key={point.month}>
                    <th scope="row" style={{ textTransform: 'capitalize' }}>
                      {formatMonth(point.month)}
                    </th>
                    <td>{formatMoney(point.income)}</td>
                    <td>{formatMoney(point.expenses)}</td>
                    <td className={toNumber(point.balance) < 0 ? 'text-negative' : 'text-positive'}>
                      {formatMoney(point.balance)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <GroupedBars
            ariaLabel="Receitas e despesas mês a mês nos últimos 12 meses"
            labels={points.map((point) => formatMonthShort(point.month))}
            series={[
              {
                id: 'receitas',
                label: 'Receitas',
                color: SEMANTIC.income,
                values: points.map((point) => toNumber(point.income)),
              },
              {
                id: 'despesas',
                label: 'Despesas',
                color: SEMANTIC.expense,
                values: points.map((point) => toNumber(point.expenses)),
              },
            ]}
          />
        )}
      </GlassCard>

      <section className="grid grid--halves">
        <GlassCard
          title="Gastos por categoria"
          subtitle={byCategory.data ? `Total de ${formatMoney(byCategory.data.total)}` : undefined}
        >
          {byCategory.loading ? (
            <Skeleton height={200} radius="var(--radius-md)" />
          ) : (byCategory.data?.items.length ?? 0) === 0 ? (
            <EmptyState
              compact
              icon={<Icon name="tag" size={26} />}
              title="Sem despesas no mês"
              message="Escolha outro mês ou registre lançamentos para ver a divisão."
            />
          ) : (
            <BarList
              total={byCategory.data?.total}
              items={(byCategory.data?.items ?? []).map((item) => ({
                id: item.category_id ?? item.name,
                name: item.name,
                amount: item.amount,
                color: item.color,
                percentage: item.percentage,
              }))}
            />
          )}
        </GlassCard>

        <GlassCard
          title="Gastos por cartão"
          subtitle={byCard.data ? `Total de ${formatMoney(byCard.data.total)}` : undefined}
        >
          {byCard.loading ? (
            <Skeleton height={200} radius="var(--radius-md)" />
          ) : (byCard.data?.items.length ?? 0) === 0 ? (
            <EmptyState
              compact
              icon={<Icon name="card" size={26} />}
              title="Nenhuma compra no cartão"
              message="As compras feitas no crédito aparecem aqui, separadas por cartão."
            />
          ) : (
            <BarList
              total={byCard.data?.total}
              items={(byCard.data?.items ?? []).map((item) => ({
                id: item.card_id,
                name: item.name,
                amount: item.amount,
                color: item.color,
                percentage: item.percentage,
              }))}
            />
          )}
        </GlassCard>
      </section>

      <section className="grid grid--halves">
        <GlassCard title="Evolução do patrimônio" subtitle="Últimos 12 meses">
          {netWorth.loading ? (
            <Skeleton height={220} radius="var(--radius-md)" />
          ) : (
            <TrendChart
              ariaLabel="Patrimônio líquido nos últimos 12 meses"
              height={220}
              labels={(netWorth.data?.points ?? []).map((point) => formatMonthShort(point.month))}
              series={[
                {
                  id: 'patrimonio',
                  label: 'Patrimônio',
                  color: SEMANTIC.balance,
                  values: (netWorth.data?.points ?? []).map((point) => toNumber(point.net_worth)),
                  area: true,
                },
              ]}
            />
          )}
        </GlassCard>

        <GlassCard
          title="Gastos recorrentes"
          subtitle="O que se repete todo mês"
          flush
        >
          {recurring.loading ? (
            <div style={{ padding: 'var(--space-6)' }}>
              <Skeleton height={180} radius="var(--radius-md)" />
            </div>
          ) : (recurring.data?.items.length ?? 0) === 0 ? (
            <EmptyState
              compact
              icon={<Icon name="repeat" size={26} />}
              title="Nenhuma recorrência"
              message="Cadastre contas fixas para medir quanto do seu mês já está comprometido."
            />
          ) : (
            <>
              <div className="record" style={{ backgroundColor: 'var(--glass-2-bg)' }}>
                <div className="record__body">
                  <p className="record__title">Comprometido por mês</p>
                  <p className="record__meta">
                    {formatMoney(recurring.data?.recurring_income)} de receita recorrente
                  </p>
                </div>
                <span className="record__amount text-negative">
                  {formatMoney(recurring.data?.recurring_expenses)}
                </span>
              </div>
              <div className="record-list">
                {recurring.data?.items.slice(0, 8).map((item) => (
                  <div key={`${item.rule_id}-${item.due_date}`} className="record">
                    <div className="record__body">
                      <p className="record__title">{item.description}</p>
                      <p className="record__meta">
                        {item.is_settled ? 'já lançado' : 'previsto'}
                      </p>
                    </div>
                    <span
                      className={`record__amount ${
                        item.type === 'income' ? 'text-positive' : 'text-negative'
                      }`}
                    >
                      {formatMoney(item.amount)}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </GlassCard>
      </section>
    </div>
  )
}

/** Último dia do mês de uma data ISO no primeiro dia. */
function lastDayOf(month: string): string {
  const [year, monthNumber] = month.split('-').map(Number)
  const date = new Date(year ?? 1970, monthNumber ?? 1, 0)
  const paddedMonth = String(date.getMonth() + 1).padStart(2, '0')
  const paddedDay = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${paddedMonth}-${paddedDay}`
}
