import { GlassCard } from '@/components/ui/GlassCard'
import { ErrorNotice, Skeleton } from '@/components/ui/Feedback'
import { Stat } from '@/components/ui/Stat'
import { Icon } from '@/components/ui/Icon'
import { TrendChart } from '@/components/charts/TrendChart'
import { SEMANTIC } from '@/components/charts/palette'
import { useAsync } from '@/hooks/useAsync'
import { accountsApi, investmentsApi, reportsApi } from '@/services/endpoints'
import { formatMoney, formatMonthShort, toNumber } from '@/utils/format'
import '@/components/ui/page.css'

export function NetWorthPage() {
  const evolution = useAsync(() => reportsApi.netWorth(12), [])
  const overview = useAsync(() => reportsApi.overview(), [])
  const accounts = useAsync(() => accountsApi.list(), [])
  const portfolio = useAsync(() => investmentsApi.portfolio(), [])

  const points = evolution.data?.points ?? []
  const composition = [
    {
      label: 'Em conta',
      value: toNumber(overview.data?.available_balance),
      color: 'var(--info)',
      icon: 'wallet' as const,
    },
    {
      label: 'Investido',
      value: toNumber(overview.data?.invested_amount),
      color: 'var(--positive)',
      icon: 'trending-up' as const,
    },
    {
      label: 'Faturas em aberto',
      value: -toNumber(overview.data?.open_invoices),
      color: 'var(--negative)',
      icon: 'card' as const,
    },
  ]

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">Patrimônio</h2>
          <p className="page__lede">Tudo que você tem, menos o que já deve.</p>
        </div>
      </div>

      {evolution.error && <ErrorNotice detail={evolution.error} />}

      <section className="grid grid--stats">
        <Stat
          label="Patrimônio líquido"
          value={formatMoney(overview.data?.net_worth)}
          hint="Contas + investimentos − faturas em aberto"
          loading={overview.loading}
          large
          icon={<Icon name="bank" size={15} />}
          iconColor="var(--accent)"
          iconBackground="var(--accent-soft)"
        />
        {composition.map((item) => (
          <Stat
            key={item.label}
            label={item.label}
            value={formatMoney(Math.abs(item.value))}
            loading={overview.loading}
            tone={item.value < 0 ? 'negative' : 'default'}
            icon={<Icon name={item.icon} size={15} />}
            iconColor={item.color}
            iconBackground={`color-mix(in srgb, ${item.color} 14%, transparent)`}
          />
        ))}
      </section>

      <GlassCard
        title="Evolução do patrimônio"
        subtitle="Reconstruída a partir do resultado de cada mês"
      >
        {evolution.loading ? (
          <Skeleton height={260} radius="var(--radius-md)" />
        ) : (
          <TrendChart
            ariaLabel="Patrimônio líquido nos últimos 12 meses"
            height={280}
            labels={points.map((point) => formatMonthShort(point.month))}
            series={[
              {
                id: 'patrimonio',
                label: 'Patrimônio',
                color: SEMANTIC.balance,
                values: points.map((point) => toNumber(point.net_worth)),
                area: true,
              },
            ]}
          />
        )}
        <p
          className="text-tertiary"
          style={{ fontSize: 'var(--text-xs)', marginTop: 'var(--space-4)' }}
        >
          Os investimentos entram pelo valor de hoje em todos os meses: esta versão ainda não
          guarda histórico de cotações.
        </p>
      </GlassCard>

      <section className="grid grid--halves">
        <GlassCard title="Onde está o dinheiro" flush>
          {accounts.loading ? (
            <div style={{ padding: 'var(--space-6)' }}>
              <Skeleton height={140} radius="var(--radius-md)" />
            </div>
          ) : (
            <div className="record-list">
              {accounts.data?.accounts.map((account) => (
                <div key={account.id} className="record">
                  <span
                    className="record__icon"
                    style={{ backgroundColor: `${account.color}1F`, color: account.color }}
                  >
                    <Icon name="wallet" size={18} />
                  </span>
                  <div className="record__body">
                    <p className="record__title">{account.name}</p>
                    <p className="record__meta">{account.bank ?? 'Sem banco informado'}</p>
                  </div>
                  <span className="record__amount">{formatMoney(account.current_balance)}</span>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        <GlassCard title="Carteira por classe" flush>
          {portfolio.loading ? (
            <div style={{ padding: 'var(--space-6)' }}>
              <Skeleton height={140} radius="var(--radius-md)" />
            </div>
          ) : (
            <div className="record-list">
              {portfolio.data?.allocation.map((slice) => (
                <div key={slice.type} className="record">
                  <div className="record__body">
                    <p className="record__title">{slice.label}</p>
                    <p className="record__meta">{slice.percentage}% da carteira</p>
                  </div>
                  <span className="record__amount">{formatMoney(slice.value)}</span>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </section>
    </div>
  )
}
