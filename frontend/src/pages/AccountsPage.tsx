import { useState } from 'react'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassInput, GlassSelect } from '@/components/ui/GlassInput'
import { GlassModal, ConfirmDialog } from '@/components/ui/GlassModal'
import { EmptyState, ErrorNotice, Skeleton } from '@/components/ui/Feedback'
import { Stat } from '@/components/ui/Stat'
import { Icon, iconOf } from '@/components/ui/Icon'
import { useToast } from '@/components/ui/Toast'
import { useAsync } from '@/hooks/useAsync'
import { accountsApi } from '@/services/endpoints'
import { ApiError } from '@/services/client'
import {
  ACCOUNT_TYPE_LABELS,
  formatMoney,
  formatMonth,
  formatPercent,
  toNumber,
  today,
} from '@/utils/format'
import type { Account } from '@/types/api'
import '@/components/ui/page.css'

const TYPES = Object.entries(ACCOUNT_TYPE_LABELS)

const ICONS = ['bank', 'wallet', 'trending-up', 'card'] as const

interface FormState {
  name: string
  bank: string
  type: string
  initial_balance: string
  icon: string
  color: string
  /** Vazio quando a conta não rende. */
  yield_rate: string
  yield_started_on: string
}

const EMPTY: FormState = {
  name: '',
  bank: '',
  type: 'checking',
  initial_balance: '0',
  icon: 'bank',
  color: '#2A78D6',
  yield_rate: '',
  yield_started_on: '',
}

export function AccountsPage() {
  const toast = useToast()
  const { data, loading, error, reload } = useAsync(() => accountsApi.list(true), [])

  const [editing, setEditing] = useState<Account | null>(null)
  const [creating, setCreating] = useState(false)
  const [form, setForm] = useState<FormState>(EMPTY)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [removing, setRemoving] = useState<Account | null>(null)

  const openCreate = () => {
    setForm(EMPTY)
    setFormError(null)
    setCreating(true)
  }

  const openEdit = (account: Account) => {
    setForm({
      name: account.name,
      bank: account.bank ?? '',
      type: account.type,
      initial_balance: account.initial_balance,
      icon: account.icon,
      color: account.color,
      yield_rate: account.yield_type === 'cdi_percent' ? account.yield_rate : '',
      yield_started_on: account.yield_started_on ?? '',
    })
    setFormError(null)
    setEditing(account)
  }

  const close = () => {
    setCreating(false)
    setEditing(null)
  }

  const save = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setFormError(null)

    // Taxa vazia significa conta que não rende — é o caso mais comum, então
    // é o padrão e não exige nenhuma escolha extra de quem só quer uma conta.
    const rate = form.yield_rate.trim()
    const payload = {
      name: form.name.trim(),
      bank: form.bank.trim() || null,
      type: form.type,
      initial_balance: form.initial_balance || '0',
      icon: form.icon,
      color: form.color,
      yield_type: rate ? 'cdi_percent' : 'none',
      yield_rate: rate || '0',
      yield_started_on: rate ? form.yield_started_on || today() : null,
    }

    try {
      if (editing) {
        await accountsApi.update(editing.id, payload)
        toast.success('Conta atualizada')
      } else {
        await accountsApi.create(payload)
        toast.success('Conta criada')
      }
      close()
      reload()
    } catch (cause) {
      setFormError(cause instanceof ApiError ? cause.message : 'Não foi possível salvar.')
    } finally {
      setSaving(false)
    }
  }

  const confirmRemove = async () => {
    if (!removing) return
    try {
      await accountsApi.remove(removing.id)
      toast.success('Conta excluída')
      setRemoving(null)
      reload()
    } catch (cause) {
      // O backend recusa excluir contas com histórico: arquivar preserva os dados.
      toast.error(
        'Não foi possível excluir',
        cause instanceof ApiError ? cause.message : undefined,
      )
      setRemoving(null)
    }
  }

  const toggleArchive = async (account: Account) => {
    await accountsApi.update(account.id, { is_archived: !account.is_archived })
    toast.success(account.is_archived ? 'Conta reativada' : 'Conta arquivada')
    reload()
  }

  const active = data?.accounts.filter((account) => !account.is_archived) ?? []
  const archived = data?.accounts.filter((account) => account.is_archived) ?? []

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">Contas</h2>
          <p className="page__lede">Onde seu dinheiro está guardado.</p>
        </div>
        <GlassButton variant="primary" onClick={openCreate}>
          <Icon name="plus" size={16} />
          Nova conta
        </GlassButton>
      </div>

      {error && <ErrorNotice detail={error} />}

      <Stat
        label="Saldo total"
        value={formatMoney(data?.total_balance)}
        hint="Somando as contas ativas"
        loading={loading}
        large
        icon={<Icon name="wallet" size={15} />}
        iconColor="var(--accent)"
        iconBackground="var(--accent-soft)"
      />

      {loading ? (
        <div className="grid grid--cards">
          <Skeleton height={132} radius="var(--radius-lg)" />
          <Skeleton height={132} radius="var(--radius-lg)" />
        </div>
      ) : active.length === 0 ? (
        <GlassCard>
          <EmptyState
            icon={<Icon name="wallet" size={28} />}
            title="Nenhuma conta cadastrada"
            message="Cadastre sua conta corrente, poupança ou carteira para começar a acompanhar seu saldo."
            action={<GlassButton onClick={openCreate}>Criar primeira conta</GlassButton>}
          />
        </GlassCard>
      ) : (
        <div className="grid grid--cards">
          {active.map((account) => (
            <AccountCard
              key={account.id}
              account={account}
              onEdit={() => openEdit(account)}
              onArchive={() => void toggleArchive(account)}
              onRemove={() => setRemoving(account)}
            />
          ))}
        </div>
      )}

      {archived.length > 0 && (
        <GlassCard title="Arquivadas" subtitle="Continuam no histórico, fora dos totais" flush>
          <div className="record-list">
            {archived.map((account) => (
              <div key={account.id} className="record">
                <span className="record__icon" style={{ backgroundColor: 'var(--glass-hairline)' }}>
                  <Icon name={iconOf(account.icon, 'bank')} size={18} />
                </span>
                <div className="record__body">
                  <p className="record__title">{account.name}</p>
                  <p className="record__meta">{formatMoney(account.current_balance)}</p>
                </div>
                <GlassButton size="sm" onClick={() => void toggleArchive(account)}>
                  Reativar
                </GlassButton>
              </div>
            ))}
          </div>
        </GlassCard>
      )}

      <GlassModal
        open={creating || editing !== null}
        onClose={close}
        title={editing ? 'Editar conta' : 'Nova conta'}
        description="Os saldos são informados por você. O app não acessa seu banco."
        footer={
          <>
            <GlassButton variant="ghost" onClick={close}>
              Cancelar
            </GlassButton>
            <GlassButton variant="primary" form="conta-form" type="submit" loading={saving}>
              Salvar
            </GlassButton>
          </>
        }
      >
        <form id="conta-form" className="form-grid" onSubmit={save}>
          {formError && (
            <div className="form-grid__full">
              <ErrorNotice title="Verifique os dados" detail={formError} />
            </div>
          )}

          <GlassInput
            label="Nome"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            placeholder="Conta corrente"
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
            label="Tipo"
            value={form.type}
            onChange={(event) => setForm({ ...form, type: event.target.value })}
          >
            {TYPES.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </GlassSelect>

          <GlassInput
            label="Saldo inicial"
            type="number"
            step="0.01"
            prefix="R$"
            value={form.initial_balance}
            onChange={(event) => setForm({ ...form, initial_balance: event.target.value })}
            hint={editing ? 'O saldo atual é recalculado a partir das transações.' : undefined}
          />

          <GlassSelect
            label="Ícone"
            value={form.icon}
            onChange={(event) => setForm({ ...form, icon: event.target.value })}
          >
            {ICONS.map((icon) => (
              <option key={icon} value={icon}>
                {icon}
              </option>
            ))}
          </GlassSelect>

          <GlassInput
            label="Cor"
            type="color"
            value={form.color}
            onChange={(event) => setForm({ ...form, color: event.target.value })}
          />

          <div className="form-grid__full" style={{ paddingTop: 'var(--space-2)' }}>
            <p
              style={{
                fontSize: 'var(--text-sm)',
                fontWeight: 'var(--weight-medium)',
                marginBottom: 'var(--space-1)',
              }}
            >
              Rendimento
            </p>
            <p className="text-tertiary" style={{ fontSize: 'var(--text-xs)' }}>
              Para contas que rendem um percentual do CDI. Deixe vazio se a conta não
              rende.
              {data?.cdi_annual_rate &&
                ` CDI hoje: ${formatPercent(data.cdi_annual_rate)} ao ano.`}
            </p>
          </div>

          <GlassInput
            label="% do CDI"
            type="number"
            step="0.01"
            min="0"
            max="1000"
            value={form.yield_rate}
            onChange={(event) => setForm({ ...form, yield_rate: event.target.value })}
            placeholder="100"
            hint="100 = 100% do CDI"
          />

          {form.yield_rate.trim() !== '' && (
            <GlassInput
              label="Rende desde"
              type="date"
              value={form.yield_started_on}
              onChange={(event) => setForm({ ...form, yield_started_on: event.target.value })}
              hint="Meses fechados são creditados automaticamente."
            />
          )}
        </form>
      </GlassModal>

      <ConfirmDialog
        open={removing !== null}
        title="Excluir conta"
        message={`A conta "${removing?.name}" será removida. Contas com transações não podem ser excluídas — arquive-a para preservar o histórico.`}
        confirmLabel="Excluir"
        destructive
        onConfirm={() => void confirmRemove()}
        onCancel={() => setRemoving(null)}
      />
    </div>
  )
}

interface AccountCardProps {
  account: Account
  onEdit: () => void
  onArchive: () => void
  onRemove: () => void
}

function AccountCard({ account, onEdit, onArchive, onRemove }: AccountCardProps) {
  const balance = toNumber(account.current_balance)

  return (
    <GlassCard compact>
      <div className="stack" style={{ gap: 'var(--space-4)' }}>
        <div className="spread">
          <span
            className="record__icon"
            style={{ backgroundColor: `${account.color}1F`, color: account.color }}
          >
            <Icon name={iconOf(account.icon, 'bank')} size={19} />
          </span>
          <div className="record__actions" style={{ opacity: 1 }}>
            <GlassButton variant="ghost" size="sm" iconOnly aria-label="Editar" onClick={onEdit}>
              <Icon name="edit" size={15} />
            </GlassButton>
            <GlassButton
              variant="ghost"
              size="sm"
              iconOnly
              aria-label="Arquivar"
              onClick={onArchive}
            >
              <Icon name="check" size={15} />
            </GlassButton>
            <GlassButton variant="ghost" size="sm" iconOnly aria-label="Excluir" onClick={onRemove}>
              <Icon name="trash" size={15} />
            </GlassButton>
          </div>
        </div>

        <div>
          <p style={{ fontWeight: 'var(--weight-medium)' }}>{account.name}</p>
          <p className="text-tertiary" style={{ fontSize: 'var(--text-xs)' }}>
            {[account.bank, ACCOUNT_TYPE_LABELS[account.type]].filter(Boolean).join(' · ')}
          </p>
        </div>

        <p
          className={`stat__value ${balance < 0 ? 'text-negative' : ''}`}
          style={{ fontSize: 'var(--text-xl)' }}
        >
          {formatMoney(balance)}
        </p>

        {account.yield_info && <YieldBadge account={account} />}
      </div>
    </GlassCard>
  )
}

/**
 * Rendimento da conta: o que já foi creditado e o que está rendendo agora.
 *
 * A distinção importa — o valor do mês corrente ainda vai crescer e não está no
 * saldo. Chamá-lo de "rendimento" sem ressalva faria a pessoa contar duas vezes.
 */
function YieldBadge({ account }: { account: Account }) {
  const info = account.yield_info
  if (!info) return null

  const projected = toNumber(info.projected_amount)

  return (
    <div
      className="stack"
      style={{
        gap: 'var(--space-1)',
        paddingTop: 'var(--space-3)',
        borderTop: '1px solid var(--glass-hairline)',
      }}
    >
      <div className="spread">
        <span className="text-secondary" style={{ fontSize: 'var(--text-xs)' }}>
          {formatPercent(account.yield_rate)} do CDI
          {info.annual_rate && ` · ${formatPercent(info.annual_rate)} a.a.`}
        </span>
        <span
          className="numeric text-positive"
          style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}
        >
          + {formatMoney(projected)}
        </span>
      </div>
      <span className="text-tertiary" style={{ fontSize: 'var(--text-xs)' }}>
        {projected > 0
          ? `rendendo neste mês · ${info.business_days} ${
              info.business_days === 1 ? 'dia útil' : 'dias úteis'
            }`
          : 'ainda sem rendimento neste mês'}
        {info.last_credited_month &&
          ` · último crédito em ${formatMonth(info.last_credited_month)}`}
      </span>
    </div>
  )
}
