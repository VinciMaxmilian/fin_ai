import { useState } from 'react'
import { Link } from 'react-router-dom'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { Stat, Segmented } from '@/components/ui/Stat'
import { Badge, EmptyState, ErrorNotice, Progress, Skeleton } from '@/components/ui/Feedback'
import { Icon } from '@/components/ui/Icon'
import { TrendChart } from '@/components/charts/TrendChart'
import { BarList } from '@/components/charts/BarList'
import { SEMANTIC } from '@/components/charts/palette'
import { useAsync } from '@/hooks/useAsync'
import { useAuth } from '@/stores/auth'
import { reportsApi } from '@/services/endpoints'
import {
  formatDateShort,
  formatMoney,
  formatMonthShort,
  formatPercent,
  formatRelativeDay,
  firstName,
  toNumber,
} from '@/utils/format'
import type { Period } from '@/types/api'
import '@/components/ui/page.css'

const PERIODS: Array<{ value: Period; label: string }> = [
  { value: '7d', label: '7 dias' },
  { value: '30d', label: '30 dias' },
  { value: '3m', label: '3 meses' },
  { value: '6m', label: '6 meses' },
  { value: '1y', label: '1 ano' },
]

export function DashboardPage() {
  const { profile } = useAuth()
  const [period, setPeriod] = useState<Period>('30d')
  const { data, loading, error, reload } = useAsync(
    () => reportsApi.dashboard(period),
    [period],
  )

  if (error) {
    return (
      <ErrorNotice
        detail={error}
        action={
          <GlassButton size="sm" onClick={reload}>
            Tentar de novo
          </GlassButton>
        }
      />
    )
  }

  const overview = data?.overview
  const saldo = toNumber(overview?.balance)

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">
            Olá, {firstName(profile?.full_name ?? null, 'tudo bem?')} 👋
          </h2>
          <p className="page__lede">Esta é a sua situação financeira hoje.</p>
        </div>
      </div>

      <section className="grid grid--stats">
        <Stat
          label="Patrimônio"
          value={formatMoney(overview?.net_worth)}
          hint="Contas + investimentos − faturas em aberto"
          loading={loading}
          large
          icon={<Icon name="bank" size={15} />}
          iconColor="var(--accent)"
          iconBackground="var(--accent-soft)"
        />
        <Stat
          label="Saldo disponível"
          value={formatMoney(overview?.available_balance)}
          hint="Somando todas as contas"
          loading={loading}
          icon={<Icon name="wallet" size={15} />}
          iconColor="var(--info)"
          iconBackground="var(--info-soft)"
        />
        <Stat
          label="Receitas do mês"
          value={formatMoney(overview?.income)}
          loading={loading}
          tone="positive"
          icon={<Icon name="arrow-up" size={15} />}
          iconColor="var(--positive)"
          iconBackground="var(--positive-soft)"
        />
        <Stat
          label="Despesas do mês"
          value={formatMoney(overview?.expenses)}
          hint={
            !loading && overview
              ? `Saldo do mês: ${saldo >= 0 ? '+' : '−'} ${formatMoney(Math.abs(saldo))}`
              : undefined
          }
          loading={loading}
          tone="negative"
          icon={<Icon name="arrow-down" size={15} />}
          iconColor="var(--negative)"
          iconBackground="var(--negative-soft)"
        />
      </section>

      <section className="grid grid--split">
        <GlassCard
          title="Fluxo financeiro"
          subtitle={
            data
              ? `Entraram ${formatMoney(data.cash_flow.total_income)} e saíram ${formatMoney(
                  data.cash_flow.total_expenses,
                )}`
              : undefined
          }
          action={
            <Segmented
              options={PERIODS}
              value={period}
              onChange={setPeriod}
              ariaLabel="Período do gráfico"
            />
          }
        >
          {loading || !data ? (
            <Skeleton height={240} radius="var(--radius-md)" />
          ) : (
            <TrendChart
              ariaLabel="Receitas e despesas ao longo do período"
              labels={data.cash_flow.points.map((point) =>
                data.cash_flow.granularity === 'day'
                  ? formatDateShort(point.date)
                  : formatMonthShort(point.date),
              )}
              series={[
                {
                  id: 'receitas',
                  label: 'Receitas',
                  color: SEMANTIC.income,
                  values: data.cash_flow.points.map((point) => toNumber(point.income)),
                  area: true,
                },
                {
                  id: 'despesas',
                  label: 'Despesas',
                  color: SEMANTIC.expense,
                  values: data.cash_flow.points.map((point) => toNumber(point.expenses)),
                },
              ]}
            />
          )}
        </GlassCard>

        <GlassCard
          title="Despesas por categoria"
          subtitle="Neste mês"
          action={
            <Link to="/relatorios">
              <GlassButton variant="ghost" size="sm" iconOnly aria-label="Ver relatórios">
                <Icon name="chevron-right" size={16} />
              </GlassButton>
            </Link>
          }
        >
          {loading || !data ? (
            <Skeleton height={200} radius="var(--radius-md)" />
          ) : data.expenses_by_category.items.length === 0 ? (
            <EmptyState
              compact
              icon={<Icon name="tag" size={26} />}
              title="Nenhuma despesa ainda"
              message="Quando você lançar gastos, eles aparecem aqui divididos por categoria."
            />
          ) : (
            <BarList
              total={data.expenses_by_category.total}
              items={data.expenses_by_category.items.map((item) => ({
                id: item.category_id ?? item.name,
                name: item.name,
                amount: item.amount,
                color: item.color,
                percentage: item.percentage,
              }))}
            />
          )}
        </GlassCard>
      </section>

      <section className="grid grid--split">
        <GlassCard title="Próximas contas" subtitle="Nos próximos 30 dias" flush>
          {loading || !data ? (
            <div style={{ padding: 'var(--space-6)' }}>
              <Skeleton height={120} radius="var(--radius-md)" />
            </div>
          ) : data.upcoming_bills.length === 0 ? (
            <EmptyState
              compact
              icon={<Icon name="calendar" size={26} />}
              title="Nada previsto"
              message="Cadastre contas recorrentes para ver aqui o que vence em seguida."
              action={
                <Link to="/recorrentes">
                  <GlassButton size="sm">Cadastrar recorrente</GlassButton>
                </Link>
              }
            />
          ) : (
            <div className="record-list">
              {data.upcoming_bills.slice(0, 6).map((bill) => (
                <div key={`${bill.kind}-${bill.reference_id}-${bill.due_date}`} className="record">
                  <span
                    className="record__icon"
                    style={{
                      backgroundColor:
                        bill.kind === 'card_invoice' ? 'var(--warning-soft)' : 'var(--info-soft)',
                      color: bill.kind === 'card_invoice' ? 'var(--warning)' : 'var(--info)',
                    }}
                  >
                    <Icon name={bill.kind === 'card_invoice' ? 'card' : 'repeat'} size={18} />
                  </span>
                  <div className="record__body">
                    <p className="record__title">{bill.description}</p>
                    <p className="record__meta">{formatRelativeDay(bill.due_date)}</p>
                  </div>
                  <span className="record__amount">{formatMoney(bill.amount)}</span>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        <GlassCard
          title="Cartões"
          action={
            <Link to="/cartoes">
              <GlassButton variant="ghost" size="sm" iconOnly aria-label="Ver cartões">
                <Icon name="chevron-right" size={16} />
              </GlassButton>
            </Link>
          }
        >
          {loading || !data ? (
            <Skeleton height={140} radius="var(--radius-md)" />
          ) : data.cards.length === 0 ? (
            <EmptyState
              compact
              icon={<Icon name="card" size={26} />}
              title="Nenhum cartão"
              message="Cadastre seus cartões para acompanhar faturas e limites."
              action={
                <Link to="/cartoes">
                  <GlassButton size="sm">Adicionar cartão</GlassButton>
                </Link>
              }
            />
          ) : (
            <div className="stack" style={{ gap: 'var(--space-5)' }}>
              {data.cards.slice(0, 3).map((card) => {
                const used = toNumber(card.used_limit)
                const limit = toNumber(card.limit_amount)
                const usedPercent = limit > 0 ? (used / limit) * 100 : 0
                return (
                  <div key={card.id} className="stack" style={{ gap: 'var(--space-2)' }}>
                    <div className="spread">
                      <span style={{ fontWeight: 'var(--weight-medium)' }}>{card.name}</span>
                      {card.current_invoice && (
                        <Badge tone={card.current_invoice.status === 'due' ? 'negative' : 'neutral'}>
                          vence {formatDateShort(card.current_invoice.due_date)}
                        </Badge>
                      )}
                    </div>
                    <div className="spread">
                      <span className="numeric" style={{ fontSize: 'var(--text-lg)' }}>
                        {formatMoney(card.current_invoice?.total ?? '0')}
                      </span>
                      <span
                        className={
                          usedPercent > 100
                            ? 'text-negative'
                            : usedPercent >= 80
                              ? 'text-warning'
                              : 'text-tertiary'
                        }
                        style={{ fontSize: 'var(--text-xs)' }}
                      >
                        {formatPercent(usedPercent)} do limite
                      </span>
                    </div>
                    <Progress
                      value={usedPercent}
                      size="sm"
                      color={
                        usedPercent > 100
                          ? 'var(--negative)'
                          : usedPercent >= 80
                            ? 'var(--warning)'
                            : card.color
                      }
                      label={`${card.name}: ${formatPercent(usedPercent)} do limite usado`}
                    />
                  </div>
                )
              })}
            </div>
          )}
        </GlassCard>
      </section>
    </div>
  )
}
