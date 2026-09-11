import { useState } from 'react'
import { GlassModal } from '@/components/ui/GlassModal'
import { GlassButton } from '@/components/ui/GlassButton'
import { Segmented } from '@/components/ui/Stat'
import { EmptyState, ErrorNotice, Skeleton } from '@/components/ui/Feedback'
import { Icon } from '@/components/ui/Icon'
import { TrendChart } from '@/components/charts/TrendChart'
import { SEMANTIC } from '@/components/charts/palette'
import { useAsync } from '@/hooks/useAsync'
import { marketApi } from '@/services/endpoints'
import { formatDate, formatDateShort, formatMoney, toNumber } from '@/utils/format'
import type { Investment } from '@/types/api'

type Range = '1mo' | '3mo' | '6mo' | '1y' | '5y'

const RANGES: Array<{ value: Range; label: string }> = [
  { value: '1mo', label: '1 mês' },
  { value: '3mo', label: '3 meses' },
  { value: '6mo', label: '6 meses' },
  { value: '1y', label: '1 ano' },
  { value: '5y', label: '5 anos' },
]

// Acima de um ano, o passo diário gera pontos demais para o gráfico.
const INTERVAL_BY_RANGE: Record<Range, string> = {
  '1mo': '1d',
  '3mo': '1d',
  '6mo': '1d',
  '1y': '1wk',
  '5y': '1mo',
}

interface AssetDetailProps {
  investment: Investment
  onClose: () => void
}

/** Histórico de preço e dividendos de um ativo da carteira. */
export function AssetDetail({ investment, onClose }: AssetDetailProps) {
  const ticker = investment.ticker ?? ''
  const [range, setRange] = useState<Range>('6mo')
  const [tab, setTab] = useState<'history' | 'dividends'>('history')

  const history = useAsync(
    () => marketApi.history(ticker, range, INTERVAL_BY_RANGE[range]),
    [ticker, range],
  )
  const dividends = useAsync(() => marketApi.dividends(ticker, 24), [ticker])

  const points = history.data ?? []
  const average = toNumber(investment.average_price)

  return (
    <GlassModal
      open
      onClose={onClose}
      wide
      title={`${ticker} · ${investment.asset}`}
      description={
        investment.long_name && investment.long_name !== investment.asset
          ? investment.long_name
          : undefined
      }
    >
      <div className="stack" style={{ gap: 'var(--space-5)', paddingBottom: 'var(--space-5)' }}>
        <div className="row" style={{ gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          <GlassButton
            size="sm"
            variant={tab === 'history' ? 'primary' : 'ghost'}
            onClick={() => setTab('history')}
          >
            Preço
          </GlassButton>
          <GlassButton
            size="sm"
            variant={tab === 'dividends' ? 'primary' : 'ghost'}
            onClick={() => setTab('dividends')}
          >
            Dividendos
          </GlassButton>
        </div>

        {tab === 'history' && (
          <>
            <div className="spread">
              <div>
                <p className="text-secondary" style={{ fontSize: 'var(--text-xs)' }}>
                  Seu preço médio
                </p>
                <p className="numeric" style={{ fontSize: 'var(--text-md)' }}>
                  {formatMoney(investment.average_price)}
                </p>
              </div>
              <Segmented
                options={RANGES}
                value={range}
                onChange={setRange}
                ariaLabel="Período do histórico"
              />
            </div>

            {history.error && <ErrorNotice detail={history.error} />}

            {history.loading ? (
              <Skeleton height={240} radius="var(--radius-md)" />
            ) : points.length === 0 ? (
              <EmptyState
                compact
                icon={<Icon name="reports" size={26} />}
                title="Sem histórico"
                message="O provedor não retornou histórico para este ativo neste período."
              />
            ) : (
              <TrendChart
                ariaLabel={`Preço de fechamento de ${ticker} no período selecionado`}
                height={250}
                labels={points.map((point) => formatDateShort(point.date))}
                series={[
                  {
                    id: 'fechamento',
                    label: 'Fechamento',
                    color: SEMANTIC.balance,
                    values: points.map((point) => toNumber(point.close)),
                    area: true,
                  },
                  // Linha de referência: onde o preço médio do usuário está em
                  // relação ao mercado. É o que responde "estou ganhando?".
                  {
                    id: 'medio',
                    label: 'Seu preço médio',
                    color: SEMANTIC.neutral,
                    values: points.map(() => average),
                  },
                ]}
              />
            )}
          </>
        )}

        {tab === 'dividends' && (
          <>
            {dividends.error && <ErrorNotice detail={dividends.error} />}

            {dividends.loading ? (
              <Skeleton height={220} radius="var(--radius-md)" />
            ) : (dividends.data?.length ?? 0) === 0 ? (
              <EmptyState
                compact
                icon={<Icon name="wallet" size={26} />}
                title="Nenhum provento registrado"
                message="O provedor não retornou pagamentos para este ativo."
              />
            ) : (
              <div className="record-list">
                {dividends.data?.map((dividend, index) => {
                  const total = toNumber(dividend.rate) * toNumber(investment.quantity)
                  return (
                    <div
                      key={`${dividend.payment_date ?? 'sem-data'}-${index}`}
                      className="record"
                      style={{ paddingInline: 0 }}
                    >
                      <div className="record__body">
                        <p className="record__title">{dividend.label ?? 'Provento'}</p>
                        <p className="record__meta">
                          {dividend.payment_date
                            ? `pago em ${formatDate(dividend.payment_date)}`
                            : 'data não informada'}
                          {' · '}
                          {formatMoney(dividend.rate)} por unidade
                        </p>
                      </div>
                      <span className="record__amount text-positive">{formatMoney(total)}</span>
                    </div>
                  )
                })}
              </div>
            )}

            <p className="text-tertiary" style={{ fontSize: 'var(--text-xs)' }}>
              O valor à direita é o provento por unidade multiplicado pela sua quantidade atual —
              uma estimativa, já que sua posição pode ter mudado desde o pagamento.
            </p>
          </>
        )}
      </div>
    </GlassModal>
  )
}
