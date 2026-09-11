import { useState } from 'react'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassInput, GlassSelect } from '@/components/ui/GlassInput'
import { GlassModal, ConfirmDialog } from '@/components/ui/GlassModal'
import { EmptyState, ErrorNotice, Skeleton } from '@/components/ui/Feedback'
import { Stat } from '@/components/ui/Stat'
import { Icon } from '@/components/ui/Icon'
import { useToast } from '@/components/ui/Toast'
import { useAsync } from '@/hooks/useAsync'
import { investmentsApi } from '@/services/endpoints'
import { ApiError } from '@/services/client'
import { StackedBar } from '@/components/charts/BarList'
import { CATEGORICAL } from '@/components/charts/palette'
import { TickerField } from '@/components/investments/TickerField'
import { AssetDetail } from '@/components/investments/AssetDetail'
import {
  INVESTMENT_TYPE_LABELS,
  formatMoney,
  formatPercent,
  formatQuantity,
  toNumber,
} from '@/utils/format'
import type { Investment, InvestmentType, Quote } from '@/types/api'
import '@/components/ui/page.css'
import '@/components/investments/ticker-field.css'

interface FormState {
  asset: string
  ticker: string
  type: InvestmentType
  quantity: string
  average_price: string
  current_price: string
  institution: string
}

const EMPTY: FormState = {
  asset: '',
  ticker: '',
  type: 'stock',
  quantity: '',
  average_price: '',
  current_price: '',
  institution: '',
}

/** Cada classe de ativo recebe uma posição fixa da paleta validada. */
const TYPE_COLORS: Record<InvestmentType, string> = {
  stock: CATEGORICAL[0]!.light,
  fii: CATEGORICAL[1]!.light,
  crypto: CATEGORICAL[3]!.light,
  fixed_income: CATEGORICAL[2]!.light,
  treasury: CATEGORICAL[6]!.light,
  etf: CATEGORICAL[4]!.light,
  other: CATEGORICAL[7]!.light,
}

/** Classes cotadas automaticamente por código. Renda fixa não tem ticker. */
const QUOTABLE: InvestmentType[] = ['stock', 'fii', 'etf', 'other']

export function InvestmentsPage() {
  const toast = useToast()
  const { data, loading, error, reload } = useAsync(() => investmentsApi.portfolio(), [])

  const [form, setForm] = useState<FormState>(EMPTY)
  const [editing, setEditing] = useState<Investment | null>(null)
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [refreshing, setRefreshing] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [removing, setRemoving] = useState<Investment | null>(null)
  const [detail, setDetail] = useState<Investment | null>(null)

  const openCreate = () => {
    setForm(EMPTY)
    setEditing(null)
    setFormError(null)
    setOpen(true)
  }

  const openEdit = (investment: Investment) => {
    setForm({
      asset: investment.asset,
      ticker: investment.ticker ?? '',
      type: investment.type,
      quantity: investment.quantity,
      average_price: investment.average_price,
      current_price: investment.current_price,
      institution: investment.institution ?? '',
    })
    setEditing(investment)
    setFormError(null)
    setOpen(true)
  }

  // Encontrou cotação: preenche o nome do ativo se ainda estiver vazio.
  const handleQuote = (quote: Quote | null) => {
    if (!quote) return
    setForm((current) =>
      current.asset.trim()
        ? current
        : { ...current, asset: quote.long_name ?? quote.short_name ?? quote.symbol },
    )
  }

  const save = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setFormError(null)

    const usesTicker = QUOTABLE.includes(form.type) && form.ticker.trim() !== ''
    const payload = {
      asset: form.asset.trim(),
      ticker: usesTicker ? form.ticker.trim().toUpperCase() : null,
      type: form.type,
      quantity: form.quantity || '0',
      average_price: form.average_price || '0',
      // Com ticker, a cotação manda; o preço manual fica como reserva.
      current_price: form.current_price || '0',
      institution: form.institution.trim() || null,
    }

    try {
      if (editing) {
        await investmentsApi.update(editing.id, payload)
        toast.success('Posição atualizada')
      } else {
        await investmentsApi.create(payload)
        toast.success('Posição adicionada')
      }
      setOpen(false)
      reload()
    } catch (cause) {
      setFormError(cause instanceof ApiError ? cause.message : 'Não foi possível salvar.')
    } finally {
      setSaving(false)
    }
  }

  const refresh = async () => {
    setRefreshing(true)
    try {
      await investmentsApi.refresh()
      toast.success('Cotações atualizadas')
      reload()
    } catch (cause) {
      toast.error(
        'Não foi possível atualizar',
        cause instanceof ApiError ? cause.message : undefined,
      )
    } finally {
      setRefreshing(false)
    }
  }

  const confirmRemove = async () => {
    if (!removing) return
    try {
      await investmentsApi.remove(removing.id)
      toast.success('Posição removida')
    } catch (cause) {
      toast.error('Não foi possível remover', cause instanceof ApiError ? cause.message : undefined)
    } finally {
      setRemoving(null)
      reload()
    }
  }

  const profit = toNumber(data?.profit)
  const market = data?.market_data
  const showTickerField = QUOTABLE.includes(form.type)

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">Investimentos</h2>
          <p className="page__lede">
            {market?.enabled
              ? 'Sua carteira, com cotações do mercado brasileiro.'
              : 'Sua carteira, atualizada por você.'}
          </p>
        </div>
        <div className="row" style={{ gap: 'var(--space-2)' }}>
          {market?.enabled && (data?.positions.length ?? 0) > 0 && (
            <GlassButton onClick={() => void refresh()} loading={refreshing}>
              <Icon name="repeat" size={16} />
              Atualizar
            </GlassButton>
          )}
          <GlassButton variant="primary" onClick={openCreate}>
            <Icon name="plus" size={16} />
            Nova posição
          </GlassButton>
        </div>
      </div>

      {error && <ErrorNotice detail={error} />}

      {market?.has_stale_quotes && (
        <div className="quote-banner">
          <Icon name="alert" size={17} className="quote-banner__icon" />
          <div>
            <strong>Cotações desatualizadas.</strong> Não conseguimos falar com o provedor de
            dados agora, então estamos mostrando os últimos preços conhecidos
            {market.oldest_quote_age_seconds !== null &&
              ` (de ${formatAge(market.oldest_quote_age_seconds)} atrás)`}
            . Sua carteira continua correta.
          </div>
        </div>
      )}

      <section className="grid grid--stats">
        <Stat
          label="Patrimônio investido"
          value={formatMoney(data?.current_value)}
          loading={loading}
          large
          icon={<Icon name="trending-up" size={15} />}
          iconColor="var(--accent)"
          iconBackground="var(--accent-soft)"
        />
        <Stat label="Total aplicado" value={formatMoney(data?.invested_amount)} loading={loading} />
        <Stat
          label="Resultado"
          value={formatMoney(data?.profit)}
          hint={data ? `${formatPercent(data.profitability)} sobre o aplicado` : undefined}
          tone={profit > 0 ? 'positive' : profit < 0 ? 'negative' : 'default'}
          loading={loading}
        />
        <Stat
          label="Cotações"
          value={
            market?.enabled ? `${market.quoted_positions} ativo(s)` : 'Manual'
          }
          hint={
            market?.enabled
              ? market.oldest_quote_age_seconds !== null
                ? `Atualizado há ${formatAge(market.oldest_quote_age_seconds)}`
                : `via ${market.provider}`
              : 'Busca automática desligada'
          }
          loading={loading}
          icon={<Icon name="calendar" size={15} />}
          iconColor="var(--info)"
          iconBackground="var(--info-soft)"
        />
      </section>

      {loading ? (
        <Skeleton height={240} radius="var(--radius-lg)" />
      ) : (data?.positions.length ?? 0) === 0 ? (
        <GlassCard>
          <EmptyState
            icon={<Icon name="trending-up" size={28} />}
            title="Carteira vazia"
            message="Informe o código do ativo (PETR4, HGLG11…) e o app busca a cotação sozinho. Renda fixa e tesouro você cadastra com o preço na mão."
            action={<GlassButton onClick={openCreate}>Adicionar posição</GlassButton>}
          />
        </GlassCard>
      ) : (
        <>
          <GlassCard title="Distribuição por classe" subtitle="Sobre o valor atual da carteira">
            <StackedBar
              segments={(data?.allocation ?? []).map((slice) => ({
                id: slice.type,
                label: slice.label,
                value: slice.value,
                color: TYPE_COLORS[slice.type as InvestmentType] ?? CATEGORICAL[7]!.light,
              }))}
            />
          </GlassCard>

          <GlassCard title="Ativos" flush>
            <div className="record-list">
              {data?.positions.map((position) => (
                <PositionRow
                  key={position.id}
                  position={position}
                  onOpen={() => setDetail(position)}
                  onEdit={() => openEdit(position)}
                  onRemove={() => setRemoving(position)}
                />
              ))}
            </div>
          </GlassCard>
        </>
      )}

      <GlassModal
        open={open}
        onClose={() => setOpen(false)}
        title={editing ? 'Editar posição' : 'Nova posição'}
        description="A quantidade e o preço médio são seus. A cotação vem do mercado."
        footer={
          <>
            <GlassButton variant="ghost" onClick={() => setOpen(false)}>
              Cancelar
            </GlassButton>
            <GlassButton variant="primary" form="investimento-form" type="submit" loading={saving}>
              Salvar
            </GlassButton>
          </>
        }
      >
        <form id="investimento-form" className="form-grid" onSubmit={save}>
          {formError && (
            <div className="form-grid__full">
              <ErrorNotice title="Verifique os dados" detail={formError} />
            </div>
          )}

          <GlassSelect
            label="Tipo"
            value={form.type}
            onChange={(event) => setForm({ ...form, type: event.target.value as InvestmentType })}
          >
            {Object.entries(INVESTMENT_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </GlassSelect>

          {form.type === 'crypto' && !market?.crypto_supported && (
            <div className="form-grid__full quote-banner quote-banner--info">
              <Icon name="alert" size={17} className="quote-banner__icon" />
              <div>
                Criptomoedas exigem um plano pago no provedor de dados. Cadastre a posição e
                informe o preço atual manualmente.
              </div>
            </div>
          )}

          {showTickerField ? (
            <TickerField
              value={form.ticker}
              onChange={(ticker) => setForm((current) => ({ ...current, ticker }))}
              onQuote={handleQuote}
            />
          ) : (
            <GlassInput
              label="Preço atual"
              type="number"
              step="0.01"
              min="0"
              prefix="R$"
              value={form.current_price}
              onChange={(event) => setForm({ ...form, current_price: event.target.value })}
              hint="Sem valor, usa o preço médio."
            />
          )}

          <GlassInput
            label="Nome do ativo"
            value={form.asset}
            onChange={(event) => setForm({ ...form, asset: event.target.value })}
            placeholder="Preenchido pela cotação, se houver"
            fieldClassName="form-grid__full"
            required
          />

          <GlassInput
            label="Quantidade"
            type="number"
            step="0.00000001"
            min="0"
            value={form.quantity}
            onChange={(event) => setForm({ ...form, quantity: event.target.value })}
            required
          />

          <GlassInput
            label="Preço médio"
            type="number"
            step="0.01"
            min="0"
            prefix="R$"
            value={form.average_price}
            onChange={(event) => setForm({ ...form, average_price: event.target.value })}
            hint="Quanto você pagou, em média, por unidade."
            required
          />

          {showTickerField && (
            <GlassInput
              label="Preço atual (reserva)"
              type="number"
              step="0.01"
              min="0"
              prefix="R$"
              value={form.current_price}
              onChange={(event) => setForm({ ...form, current_price: event.target.value })}
              hint="Usado só se não houver cotação para o código."
            />
          )}

          <GlassInput
            label="Instituição"
            value={form.institution}
            onChange={(event) => setForm({ ...form, institution: event.target.value })}
            placeholder="Opcional"
          />
        </form>
      </GlassModal>

      {detail && <AssetDetail investment={detail} onClose={() => setDetail(null)} />}

      <ConfirmDialog
        open={removing !== null}
        title="Remover posição"
        message={`A posição em "${removing?.asset}" será removida da carteira. Esta ação não pode ser desfeita.`}
        confirmLabel="Remover"
        destructive
        onConfirm={() => void confirmRemove()}
        onCancel={() => setRemoving(null)}
      />
    </div>
  )
}

interface PositionRowProps {
  position: Investment
  onOpen: () => void
  onEdit: () => void
  onRemove: () => void
}

function PositionRow({ position, onOpen, onEdit, onRemove }: PositionRowProps) {
  const profit = toNumber(position.profit)
  const dayChange = toNumber(position.day_change_percent)

  return (
    <div className="record record--interactive">
      <span
        className="record__icon"
        style={{
          backgroundColor: `${TYPE_COLORS[position.type]}1F`,
          color: TYPE_COLORS[position.type],
        }}
      >
        <Icon name="trending-up" size={18} />
      </span>

      <div className="record__body">
        <p className="record__title">
          {position.ticker ? `${position.ticker} · ${position.asset}` : position.asset}
        </p>
        <p className="record__meta">
          {INVESTMENT_TYPE_LABELS[position.type]} · {formatQuantity(position.quantity)} ×{' '}
          {formatMoney(position.average_price)}
          {position.institution && ` · ${position.institution}`}
        </p>
        <PriceSourceHint position={position} />
      </div>

      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <p className="record__amount">{formatMoney(position.current_value)}</p>
        <p
          className={`numeric ${
            profit > 0 ? 'text-positive' : profit < 0 ? 'text-negative' : 'text-tertiary'
          }`}
          style={{ fontSize: 'var(--text-xs)' }}
        >
          {profit >= 0 ? '+' : '−'} {formatMoney(Math.abs(profit))} (
          {formatPercent(position.profitability)})
        </p>
        {position.day_change_percent !== null && (
          <p
            className={`numeric ${dayChange >= 0 ? 'text-positive' : 'text-negative'}`}
            style={{ fontSize: 'var(--text-xs)', opacity: 0.75 }}
          >
            hoje {dayChange >= 0 ? '+' : ''}
            {formatPercent(position.day_change_percent)}
          </p>
        )}
      </div>

      <div className="record__actions">
        {position.ticker && (
          <GlassButton
            variant="ghost"
            size="sm"
            iconOnly
            aria-label="Ver detalhes do ativo"
            onClick={onOpen}
          >
            <Icon name="reports" size={15} />
          </GlassButton>
        )}
        <GlassButton variant="ghost" size="sm" iconOnly aria-label="Editar" onClick={onEdit}>
          <Icon name="edit" size={15} />
        </GlassButton>
        <GlassButton variant="ghost" size="sm" iconOnly aria-label="Remover" onClick={onRemove}>
          <Icon name="trash" size={15} />
        </GlassButton>
      </div>
    </div>
  )
}

/** Diz de onde veio o preço, para o número nunca parecer mais certo do que é. */
function PriceSourceHint({ position }: { position: Investment }) {
  if (position.price_source === 'quote') return null

  const label =
    position.price_source === 'stale_quote'
      ? `cotação de ${position.quote_age_seconds !== null ? formatAge(position.quote_age_seconds) : 'algum tempo'} atrás`
      : position.price_source === 'manual'
        ? 'preço informado por você'
        : 'sem cotação — usando o preço médio'

  return (
    <span className="price-source">
      <Icon name="alert" size={11} />
      {label}
    </span>
  )
}

function formatAge(seconds: number): string {
  if (seconds < 60) return 'menos de um minuto'
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${minutes} min`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} h`
  return `${Math.round(hours / 24)} dias`
}

export { formatAge }
