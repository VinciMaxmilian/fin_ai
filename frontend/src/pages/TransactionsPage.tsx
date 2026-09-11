import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassInput, GlassSelect, GlassTextarea } from '@/components/ui/GlassInput'
import { GlassModal, ConfirmDialog } from '@/components/ui/GlassModal'
import { EmptyState, ErrorNotice, Skeleton } from '@/components/ui/Feedback'
import { Icon, iconOf } from '@/components/ui/Icon'
import { useToast } from '@/components/ui/Toast'
import { useAsync } from '@/hooks/useAsync'
import { useDebounced } from '@/hooks/useDebounced'
import {
  accountsApi,
  cardsApi,
  categoriesApi,
  transactionsApi,
} from '@/services/endpoints'
import { ApiError } from '@/services/client'
import {
  TRANSACTION_TYPE_LABELS,
  formatMoney,
  formatRelativeDay,
  today,
} from '@/utils/format'
import type { Transaction, TransactionQuery, TransactionType } from '@/types/api'
import '@/components/ui/page.css'

const PAGE_SIZE = 25

interface FormState {
  type: TransactionType
  amount: string
  description: string
  date: string
  category_id: string
  account_id: string
  card_id: string
  transfer_account_id: string
  installments: string
  notes: string
  /** Onde o lançamento é debitado. Muda quais campos o formulário mostra. */
  origin: 'account' | 'card'
}

function emptyForm(): FormState {
  return {
    type: 'expense',
    amount: '',
    description: '',
    date: today(),
    category_id: '',
    account_id: '',
    card_id: '',
    transfer_account_id: '',
    installments: '1',
    notes: '',
    origin: 'account',
  }
}

export function TransactionsPage() {
  const toast = useToast()
  const [searchParams, setSearchParams] = useSearchParams()

  const [filters, setFilters] = useState<TransactionQuery>({
    sort_by: 'date',
    sort_order: 'desc',
  })
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounced(search, 300)

  const accounts = useAsync(() => accountsApi.list(), [])
  const cards = useAsync(() => cardsApi.list(), [])
  const categories = useAsync(() => categoriesApi.list(), [])

  const query = useMemo<TransactionQuery>(
    () => ({
      ...filters,
      search: debouncedSearch || undefined,
      page,
      page_size: PAGE_SIZE,
    }),
    [filters, debouncedSearch, page],
  )

  const transactions = useAsync(
    (signal) => transactionsApi.list(query, signal),
    [JSON.stringify(query)],
  )

  const [form, setForm] = useState<FormState>(emptyForm)
  const [editing, setEditing] = useState<Transaction | null>(null)
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [removing, setRemoving] = useState<Transaction | null>(null)

  // A barra superior e o botão do celular abrem o formulário via ?novo=1.
  useEffect(() => {
    if (searchParams.get('novo') === '1') {
      setForm(emptyForm())
      setEditing(null)
      setFormError(null)
      setOpen(true)
      searchParams.delete('novo')
      setSearchParams(searchParams, { replace: true })
    }
  }, [searchParams, setSearchParams])

  const openCreate = () => {
    setForm(emptyForm())
    setEditing(null)
    setFormError(null)
    setOpen(true)
  }

  const openEdit = (transaction: Transaction) => {
    setForm({
      type: transaction.type,
      amount: transaction.amount,
      description: transaction.description,
      date: transaction.date,
      category_id: transaction.category_id ?? '',
      account_id: transaction.account_id ?? '',
      card_id: transaction.card_id ?? '',
      transfer_account_id: transaction.transfer_account_id ?? '',
      installments: '1',
      notes: transaction.notes ?? '',
      origin: transaction.card_id ? 'card' : 'account',
    })
    setEditing(transaction)
    setFormError(null)
    setOpen(true)
  }

  const save = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setFormError(null)

    const usesCard = form.type === 'expense' && form.origin === 'card'
    const payload = {
      type: form.type,
      amount: form.amount,
      description: form.description.trim(),
      date: form.date,
      category_id: form.category_id || null,
      account_id: usesCard ? null : form.account_id || null,
      card_id: usesCard ? form.card_id || null : null,
      transfer_account_id: form.type === 'transfer' ? form.transfer_account_id || null : null,
      notes: form.notes.trim() || null,
    }

    try {
      if (editing) {
        await transactionsApi.update(editing.id, payload)
        toast.success('Lançamento atualizado')
      } else {
        const parcels = Math.max(1, Number(form.installments) || 1)
        const created = await transactionsApi.create({ ...payload, installments: parcels })
        toast.success(
          parcels > 1 ? `${created.length} parcelas criadas` : 'Lançamento criado',
        )
      }
      setOpen(false)
      transactions.reload()
    } catch (cause) {
      setFormError(cause instanceof ApiError ? cause.message : 'Não foi possível salvar.')
    } finally {
      setSaving(false)
    }
  }

  const confirmRemove = async () => {
    if (!removing) return
    try {
      await transactionsApi.remove(removing.id)
      toast.success('Lançamento excluído')
    } catch (cause) {
      toast.error('Não foi possível excluir', cause instanceof ApiError ? cause.message : undefined)
    } finally {
      setRemoving(null)
      transactions.reload()
    }
  }

  const updateFilter = (patch: Partial<TransactionQuery>) => {
    setPage(1)
    setFilters((current) => ({ ...current, ...patch }))
  }

  const grouped = useMemo(() => groupByDate(transactions.data?.items ?? []), [transactions.data])
  const hasFilters = Boolean(
    filters.type || filters.category_id || filters.account_id || filters.card_id ||
      filters.date_from || filters.date_to || debouncedSearch,
  )

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">Transações</h2>
          <p className="page__lede">Tudo que entrou e saiu.</p>
        </div>
        <GlassButton variant="primary" onClick={openCreate}>
          <Icon name="plus" size={16} />
          Novo lançamento
        </GlassButton>
      </div>

      <GlassCard compact>
        <div className="filter-bar">
          <GlassInput
            label="Buscar"
            placeholder="Descrição ou observação"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            fieldClassName="filter-bar__search"
          />
          <GlassSelect
            label="Tipo"
            value={filters.type ?? ''}
            onChange={(event) =>
              updateFilter({ type: (event.target.value || undefined) as TransactionType })
            }
          >
            <option value="">Todos</option>
            {Object.entries(TRANSACTION_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </GlassSelect>
          <GlassSelect
            label="Categoria"
            value={filters.category_id ?? ''}
            onChange={(event) => updateFilter({ category_id: event.target.value || undefined })}
          >
            <option value="">Todas</option>
            {categories.data?.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </GlassSelect>
          <GlassSelect
            label="Conta"
            value={filters.account_id ?? ''}
            onChange={(event) => updateFilter({ account_id: event.target.value || undefined })}
          >
            <option value="">Todas</option>
            {accounts.data?.accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </GlassSelect>
          <GlassInput
            label="De"
            type="date"
            value={filters.date_from ?? ''}
            onChange={(event) => updateFilter({ date_from: event.target.value || undefined })}
          />
          <GlassInput
            label="Até"
            type="date"
            value={filters.date_to ?? ''}
            onChange={(event) => updateFilter({ date_to: event.target.value || undefined })}
          />
          <GlassSelect
            label="Ordenar"
            value={`${filters.sort_by}:${filters.sort_order}`}
            onChange={(event) => {
              const [sortBy, sortOrder] = event.target.value.split(':')
              updateFilter({
                sort_by: sortBy as TransactionQuery['sort_by'],
                sort_order: sortOrder as TransactionQuery['sort_order'],
              })
            }}
          >
            <option value="date:desc">Mais recentes</option>
            <option value="date:asc">Mais antigas</option>
            <option value="amount:desc">Maior valor</option>
            <option value="amount:asc">Menor valor</option>
            <option value="description:asc">Descrição (A–Z)</option>
          </GlassSelect>

          {hasFilters && (
            <GlassButton
              variant="ghost"
              onClick={() => {
                setSearch('')
                setPage(1)
                setFilters({ sort_by: 'date', sort_order: 'desc' })
              }}
            >
              Limpar
            </GlassButton>
          )}
        </div>
      </GlassCard>

      {transactions.error && <ErrorNotice detail={transactions.error} />}

      <GlassCard flush>
        {transactions.loading ? (
          <div style={{ padding: 'var(--space-6)' }}>
            <Skeleton height={240} radius="var(--radius-md)" />
          </div>
        ) : grouped.length === 0 ? (
          <EmptyState
            icon={<Icon name="transactions" size={28} />}
            title={hasFilters ? 'Nada encontrado' : 'Nenhum lançamento ainda'}
            message={
              hasFilters
                ? 'Nenhuma transação corresponde aos filtros. Tente ampliar o período ou limpar os filtros.'
                : 'Registre sua primeira receita ou despesa para começar a enxergar para onde vai seu dinheiro.'
            }
            action={
              hasFilters ? undefined : (
                <GlassButton onClick={openCreate}>Criar lançamento</GlassButton>
              )
            }
          />
        ) : (
          <div className="record-list">
            {grouped.map(([date, items]) => (
              <div key={date}>
                <p className="record-group__label">{formatRelativeDay(date)}</p>
                {items.map((transaction) => (
                  <TransactionRow
                    key={transaction.id}
                    transaction={transaction}
                    onEdit={() => openEdit(transaction)}
                    onRemove={() => setRemoving(transaction)}
                  />
                ))}
              </div>
            ))}
          </div>
        )}

        {transactions.data && transactions.data.pages > 1 && (
          <div className="pagination">
            <span>
              Página {transactions.data.page} de {transactions.data.pages} ·{' '}
              {transactions.data.total} lançamentos
            </span>
            <div className="row" style={{ gap: 'var(--space-2)' }}>
              <GlassButton
                size="sm"
                iconOnly
                aria-label="Página anterior"
                disabled={page <= 1}
                onClick={() => setPage((value) => value - 1)}
              >
                <Icon name="chevron-left" size={15} />
              </GlassButton>
              <GlassButton
                size="sm"
                iconOnly
                aria-label="Próxima página"
                disabled={page >= transactions.data.pages}
                onClick={() => setPage((value) => value + 1)}
              >
                <Icon name="chevron-right" size={15} />
              </GlassButton>
            </div>
          </div>
        )}
      </GlassCard>

      <GlassModal
        open={open}
        onClose={() => setOpen(false)}
        title={editing ? 'Editar lançamento' : 'Novo lançamento'}
        footer={
          <>
            <GlassButton variant="ghost" onClick={() => setOpen(false)}>
              Cancelar
            </GlassButton>
            <GlassButton variant="primary" form="transacao-form" type="submit" loading={saving}>
              Salvar
            </GlassButton>
          </>
        }
      >
        <form id="transacao-form" className="form-grid" onSubmit={save}>
          {formError && (
            <div className="form-grid__full">
              <ErrorNotice title="Verifique os dados" detail={formError} />
            </div>
          )}

          <GlassSelect
            label="Tipo"
            value={form.type}
            onChange={(event) =>
              setForm({ ...form, type: event.target.value as TransactionType, origin: 'account' })
            }
          >
            {Object.entries(TRANSACTION_TYPE_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </GlassSelect>

          <GlassInput
            label="Valor"
            type="number"
            step="0.01"
            min="0.01"
            prefix="R$"
            value={form.amount}
            onChange={(event) => setForm({ ...form, amount: event.target.value })}
            required
          />

          <GlassInput
            label="Descrição"
            value={form.description}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
            placeholder="Mercado, aluguel, salário…"
            fieldClassName="form-grid__full"
            required
          />

          <GlassInput
            label="Data"
            type="date"
            value={form.date}
            onChange={(event) => setForm({ ...form, date: event.target.value })}
            required
          />

          {form.type !== 'transfer' && (
            <GlassSelect
              label="Categoria"
              value={form.category_id}
              onChange={(event) => setForm({ ...form, category_id: event.target.value })}
            >
              <option value="">Sem categoria</option>
              {categories.data
                ?.filter(
                  (category) =>
                    category.kind === 'both' ||
                    (form.type === 'income' ? category.kind === 'income' : category.kind === 'expense'),
                )
                .map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
            </GlassSelect>
          )}

          {form.type === 'expense' && (
            <GlassSelect
              label="Pago com"
              value={form.origin}
              onChange={(event) =>
                setForm({ ...form, origin: event.target.value as FormState['origin'] })
              }
            >
              <option value="account">Conta</option>
              <option value="card">Cartão de crédito</option>
            </GlassSelect>
          )}

          {form.type === 'expense' && form.origin === 'card' ? (
            <GlassSelect
              label="Cartão"
              value={form.card_id}
              onChange={(event) => setForm({ ...form, card_id: event.target.value })}
              required
            >
              <option value="">Selecione</option>
              {cards.data?.map((card) => (
                <option key={card.id} value={card.id}>
                  {card.name}
                </option>
              ))}
            </GlassSelect>
          ) : (
            <GlassSelect
              label={form.type === 'transfer' ? 'Conta de origem' : 'Conta'}
              value={form.account_id}
              onChange={(event) => setForm({ ...form, account_id: event.target.value })}
              required
            >
              <option value="">Selecione</option>
              {accounts.data?.accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.name}
                </option>
              ))}
            </GlassSelect>
          )}

          {form.type === 'transfer' && (
            <GlassSelect
              label="Conta de destino"
              value={form.transfer_account_id}
              onChange={(event) => setForm({ ...form, transfer_account_id: event.target.value })}
              required
            >
              <option value="">Selecione</option>
              {accounts.data?.accounts
                .filter((account) => account.id !== form.account_id)
                .map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
            </GlassSelect>
          )}

          {!editing && form.type === 'expense' && (
            <GlassInput
              label="Parcelas"
              type="number"
              min="1"
              max="120"
              value={form.installments}
              onChange={(event) => setForm({ ...form, installments: event.target.value })}
              hint="Acima de 1, o valor é dividido e cada parcela vira um lançamento."
            />
          )}

          <GlassTextarea
            label="Observação"
            value={form.notes}
            onChange={(event) => setForm({ ...form, notes: event.target.value })}
            placeholder="Opcional"
            fieldClassName="form-grid__full"
          />
        </form>
      </GlassModal>

      <ConfirmDialog
        open={removing !== null}
        title="Excluir lançamento"
        message={`"${removing?.description}" será removido e os saldos serão recalculados. Esta ação não pode ser desfeita.`}
        confirmLabel="Excluir"
        destructive
        onConfirm={() => void confirmRemove()}
        onCancel={() => setRemoving(null)}
      />
    </div>
  )
}

function TransactionRow({
  transaction,
  onEdit,
  onRemove,
}: {
  transaction: Transaction
  onEdit: () => void
  onRemove: () => void
}) {
  const color = transaction.category?.color ?? 'var(--text-tertiary)'
  const sign = transaction.type === 'income' ? '+' : transaction.type === 'expense' ? '−' : ''

  return (
    <div className="record record--interactive">
      <span
        className="record__icon"
        style={{
          backgroundColor: transaction.category ? `${color}1F` : 'var(--glass-hairline)',
          color,
        }}
      >
        <Icon
          name={
            transaction.type === 'transfer'
              ? 'arrow-swap'
              : iconOf(transaction.category?.icon, transaction.type === 'income' ? 'wallet' : 'tag')
          }
          size={18}
        />
      </span>

      <div className="record__body">
        <p className="record__title">{transaction.description}</p>
        <p className="record__meta">
          {transaction.category?.name ?? TRANSACTION_TYPE_LABELS[transaction.type]}
          {transaction.installment_number &&
            ` · parcela ${transaction.installment_number}`}
        </p>
      </div>

      <span
        className={`record__amount ${
          transaction.type === 'income'
            ? 'text-positive'
            : transaction.type === 'expense'
              ? 'text-negative'
              : ''
        }`}
      >
        {sign} {formatMoney(transaction.amount)}
      </span>

      <div className="record__actions">
        <GlassButton variant="ghost" size="sm" iconOnly aria-label="Editar" onClick={onEdit}>
          <Icon name="edit" size={15} />
        </GlassButton>
        <GlassButton variant="ghost" size="sm" iconOnly aria-label="Excluir" onClick={onRemove}>
          <Icon name="trash" size={15} />
        </GlassButton>
      </div>
    </div>
  )
}

/** Agrupa por data preservando a ordem que o backend devolveu. */
function groupByDate(items: Transaction[]): Array<[string, Transaction[]]> {
  const groups = new Map<string, Transaction[]>()
  for (const item of items) {
    const bucket = groups.get(item.date)
    if (bucket) bucket.push(item)
    else groups.set(item.date, [item])
  }
  return [...groups.entries()]
}
