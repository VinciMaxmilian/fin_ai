import { useState } from 'react'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassInput, GlassSelect } from '@/components/ui/GlassInput'
import { GlassModal, ConfirmDialog } from '@/components/ui/GlassModal'
import { Badge, EmptyState, ErrorNotice, Progress, Skeleton } from '@/components/ui/Feedback'
import { Icon } from '@/components/ui/Icon'
import { CardVisual } from '@/components/cards/CardVisual'
import { useToast } from '@/components/ui/Toast'
import { useAsync } from '@/hooks/useAsync'
import { accountsApi, cardsApi } from '@/services/endpoints'
import { ApiError } from '@/services/client'
import { cx } from '@/utils/cx'
import {
  CARD_BRAND_LABELS,
  INVOICE_STATUS_LABELS,
  formatDate,
  formatDateShort,
  formatMoney,
  formatPercent,
  toNumber,
} from '@/utils/format'
import type { Card, Invoice } from '@/types/api'
import '@/components/ui/page.css'

interface FormState {
  name: string
  bank: string
  brand: string
  limit_amount: string
  closing_day: string
  due_day: string
  account_id: string
  color: string
}

const EMPTY: FormState = {
  name: '',
  bank: '',
  brand: 'other',
  limit_amount: '0',
  closing_day: '1',
  due_day: '10',
  account_id: '',
  color: '#1C1C1E',
}

export function CardsPage() {
  const toast = useToast()
  const cards = useAsync(() => cardsApi.list(), [])
  const accounts = useAsync(() => accountsApi.list(), [])

  const [editing, setEditing] = useState<Card | null>(null)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState<FormState>(EMPTY)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [removing, setRemoving] = useState<Card | null>(null)
  const [detail, setDetail] = useState<Card | null>(null)

  const openCreate = () => {
    setForm(EMPTY)
    setFormError(null)
    setCreating(true)
  }

  const openEdit = (card: Card) => {
    setForm({
      name: card.name,
      bank: card.bank ?? '',
      brand: card.brand,
      limit_amount: card.limit_amount,
      closing_day: String(card.closing_day),
      due_day: String(card.due_day),
      account_id: card.account_id ?? '',
      color: card.color,
    })
    setFormError(null)
    setEditing(card)
  }

  const close = () => {
    setCreating(false)
    setEditing(null)
  }

  const save = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setFormError(null)

    const payload = {
      name: form.name.trim(),
      bank: form.bank.trim() || null,
      brand: form.brand,
      limit_amount: form.limit_amount || '0',
      closing_day: Number(form.closing_day),
      due_day: Number(form.due_day),
      account_id: form.account_id || null,
      color: form.color,
    }

    try {
      if (editing) {
        await cardsApi.update(editing.id, payload)
        toast.success('Cartão atualizado')
      } else {
        await cardsApi.create(payload)
        toast.success('Cartão criado')
      }
      close()
      cards.reload()
    } catch (cause) {
      setFormError(cause instanceof ApiError ? cause.message : 'Não foi possível salvar.')
    } finally {
      setSaving(false)
    }
  }

  const confirmRemove = async () => {
    if (!removing) return
    try {
      await cardsApi.remove(removing.id)
      toast.success('Cartão excluído')
    } catch (cause) {
      toast.error('Não foi possível excluir', cause instanceof ApiError ? cause.message : undefined)
    } finally {
      setRemoving(null)
      cards.reload()
    }
  }

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">Cartões</h2>
          <p className="page__lede">Faturas, limites e parcelas em andamento.</p>
        </div>
        <GlassButton variant="primary" onClick={openCreate}>
          <Icon name="plus" size={16} />
          Novo cartão
        </GlassButton>
      </div>

      {cards.error && <ErrorNotice detail={cards.error} />}

      {cards.loading ? (
        <div className="grid grid--cards">
          <Skeleton height={196} radius="var(--radius-lg)" />
          <Skeleton height={196} radius="var(--radius-lg)" />
        </div>
      ) : (cards.data?.length ?? 0) === 0 ? (
        <GlassCard>
          <EmptyState
            icon={<Icon name="card" size={28} />}
            title="Nenhum cartão cadastrado"
            message="Informe o limite e os dias de fechamento e vencimento — o app monta as faturas a partir das suas compras."
            action={<GlassButton onClick={openCreate}>Adicionar cartão</GlassButton>}
          />
        </GlassCard>
      ) : (
        <div className="grid grid--cards">
          {cards.data?.map((card) => (
            <CreditCardTile
              key={card.id}
              card={card}
              onEdit={() => openEdit(card)}
              onRemove={() => setRemoving(card)}
              onOpenInvoices={() => setDetail(card)}
            />
          ))}
        </div>
      )}

      <GlassModal
        open={creating || editing !== null}
        onClose={close}
        title={editing ? 'Editar cartão' : 'Novo cartão'}
        footer={
          <>
            <GlassButton variant="ghost" onClick={close}>
              Cancelar
            </GlassButton>
            <GlassButton variant="primary" form="cartao-form" type="submit" loading={saving}>
              Salvar
            </GlassButton>
          </>
        }
      >
        <form id="cartao-form" className="form-grid" onSubmit={save}>
          {formError && (
            <div className="form-grid__full">
              <ErrorNotice title="Verifique os dados" detail={formError} />
            </div>
          )}

          {/* Prévia ao vivo: cor e bandeira são escolhidas aqui embaixo, então
              ver o resultado na hora evita salvar e voltar para corrigir. */}
          <div
            className="form-grid__full"
            style={{ display: 'flex', justifyContent: 'center', paddingBottom: 'var(--space-2)' }}
          >
            <CardVisual
              name={form.name.trim() || 'Seu cartão'}
              brand={form.brand as Card['brand']}
              color={form.color}
              bank={form.bank.trim() || null}
            />
          </div>

          <GlassInput
            label="Nome"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            placeholder="Cartão Itaú"
            fieldClassName="form-grid__full"
            required
            autoFocus
          />

          <GlassInput
            label="Banco"
            value={form.bank}
            onChange={(event) => setForm({ ...form, bank: event.target.value })}
            placeholder="Opcional"
          />

          <GlassSelect
            label="Bandeira"
            value={form.brand}
            onChange={(event) => setForm({ ...form, brand: event.target.value })}
          >
            {Object.entries(CARD_BRAND_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </GlassSelect>

          <GlassInput
            label="Limite"
            type="number"
            step="0.01"
            min="0"
            prefix="R$"
            value={form.limit_amount}
            onChange={(event) => setForm({ ...form, limit_amount: event.target.value })}
          />

          <GlassSelect
            label="Conta do débito"
            value={form.account_id}
            onChange={(event) => setForm({ ...form, account_id: event.target.value })}
            hint="De onde a fatura é paga"
          >
            <option value="">Nenhuma</option>
            {accounts.data?.accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </GlassSelect>

          <GlassInput
            label="Dia do fechamento"
            type="number"
            min="1"
            max="31"
            value={form.closing_day}
            onChange={(event) => setForm({ ...form, closing_day: event.target.value })}
            required
          />

          <GlassInput
            label="Dia do vencimento"
            type="number"
            min="1"
            max="31"
            value={form.due_day}
            onChange={(event) => setForm({ ...form, due_day: event.target.value })}
            hint="Compras após o fechamento entram na fatura seguinte."
            required
          />

          <GlassInput
            label="Cor"
            type="color"
            value={form.color}
            onChange={(event) => setForm({ ...form, color: event.target.value })}
          />
        </form>
      </GlassModal>

      {detail && <InvoicesModal card={detail} onClose={() => setDetail(null)} />}

      <ConfirmDialog
        open={removing !== null}
        title="Excluir cartão"
        message={`Excluir "${removing?.name}" remove também todas as compras e parcelas lançadas nele. Esta ação não pode ser desfeita.`}
        confirmLabel="Excluir cartão"
        destructive
        onConfirm={() => void confirmRemove()}
        onCancel={() => setRemoving(null)}
      />
    </div>
  )
}

interface TileProps {
  card: Card
  onEdit: () => void
  onRemove: () => void
  onOpenInvoices: () => void
}

function CreditCardTile({ card, onEdit, onRemove, onOpenInvoices }: TileProps) {
  const used = toNumber(card.used_limit)
  const limit = toNumber(card.limit_amount)
  const invoice = card.current_invoice
  const usedPercent = limit > 0 ? (used / limit) * 100 : 0
  const overLimit = used > limit
  // A partir de 80% o limite vira informação de alerta, não só de status.
  const nearLimit = !overLimit && usedPercent >= 80

  return (
    <GlassCard compact>
      <div className="stack" style={{ gap: 'var(--space-4)' }}>
        {/* As ações flutuam sobre o canto do cartão: ocupar uma linha só para
            elas roubaria espaço do que importa, que é a fatura. */}
        <div style={{ position: 'relative' }}>
          <CardVisual
            name={card.name}
            brand={card.brand}
            color={card.color}
            bank={card.bank}
            muted={card.is_archived}
          />
          <div
            className="record__actions"
            style={{ position: 'absolute', top: 0, right: 0, opacity: 1 }}
          >
            <GlassButton variant="ghost" size="sm" iconOnly aria-label="Editar" onClick={onEdit}>
              <Icon name="edit" size={15} />
            </GlassButton>
            <GlassButton variant="ghost" size="sm" iconOnly aria-label="Excluir" onClick={onRemove}>
              <Icon name="trash" size={15} />
            </GlassButton>
          </div>
        </div>

        <div>
          <p className="text-secondary" style={{ fontSize: 'var(--text-xs)' }}>
            Fatura atual
          </p>
          <p className="stat__value" style={{ fontSize: 'var(--text-xl)' }}>
            {formatMoney(invoice?.total ?? '0')}
          </p>
        </div>

        <div className="stack" style={{ gap: 'var(--space-2)' }}>
          <div className="spread" style={{ fontSize: 'var(--text-xs)' }}>
            <span className="text-secondary">Limite usado</span>
            <span
              className={cx(
                'numeric',
                overLimit ? 'text-negative' : nearLimit ? 'text-warning' : 'text-secondary',
              )}
              style={{ fontWeight: 'var(--weight-semibold)' }}
            >
              {formatPercent(usedPercent)}
            </span>
          </div>

          <Progress
            value={usedPercent}
            size="sm"
            color={overLimit ? 'var(--negative)' : nearLimit ? 'var(--warning)' : card.color}
            label={`${card.name}: ${formatPercent(usedPercent)} do limite usado`}
          />

          <div className="spread" style={{ fontSize: 'var(--text-xs)' }}>
            <span className="text-tertiary">
              {formatMoney(card.used_limit)} de {formatMoney(card.limit_amount)}
            </span>
            {overLimit ? (
              <Badge tone="negative">Acima do limite</Badge>
            ) : (
              <span className="text-tertiary">
                {formatMoney(card.available_limit)} disponíveis
              </span>
            )}
          </div>
        </div>

        <div className="spread">
          {invoice && (
            <Badge tone={invoice.status === 'due' ? 'negative' : 'neutral'}>
              {INVOICE_STATUS_LABELS[invoice.status]} · vence {formatDateShort(invoice.due_date)}
            </Badge>
          )}
          <GlassButton variant="ghost" size="sm" onClick={onOpenInvoices}>
            Faturas
            <Icon name="chevron-right" size={14} />
          </GlassButton>
        </div>
      </div>
    </GlassCard>
  )
}

function InvoicesModal({ card, onClose }: { card: Card; onClose: () => void }) {
  const { data, loading, error } = useAsync(() => cardsApi.invoices(card.id, 6), [card.id])

  return (
    <GlassModal
      open
      onClose={onClose}
      title={`Faturas · ${card.name}`}
      description="A fatura atual e as próximas, já contando as parcelas futuras."
    >
      {error && <ErrorNotice detail={error} />}
      {loading ? (
        <Skeleton height={180} radius="var(--radius-md)" />
      ) : (
        <div className="record-list" style={{ paddingBottom: 'var(--space-4)' }}>
          {data?.map((invoice: Invoice) => (
            <div key={invoice.closing_date} className="record" style={{ paddingInline: 0 }}>
              <div className="record__body">
                <p className="record__title">Vence {formatDate(invoice.due_date)}</p>
                <p className="record__meta">
                  {formatDateShort(invoice.period_start)} a {formatDateShort(invoice.period_end)}
                  {invoice.transactions_count > 0 && ` · ${invoice.transactions_count} compras`}
                </p>
              </div>
              <span className="record__amount">{formatMoney(invoice.total)}</span>
            </div>
          ))}
        </div>
      )}
    </GlassModal>
  )
}
