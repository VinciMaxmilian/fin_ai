import { useState } from 'react'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassInput, GlassSelect } from '@/components/ui/GlassInput'
import { GlassModal, ConfirmDialog } from '@/components/ui/GlassModal'
import { Badge, EmptyState, ErrorNotice, Skeleton } from '@/components/ui/Feedback'
import { Stat } from '@/components/ui/Stat'
import { Icon } from '@/components/ui/Icon'
import { useToast } from '@/components/ui/Toast'
import { useAsync } from '@/hooks/useAsync'
import { accountsApi, categoriesApi, recurringApi, reportsApi } from '@/services/endpoints'
import { ApiError } from '@/services/client'
import {
  FREQUENCY_LABELS,
  addMonths,
  formatMoney,
  formatRelativeDay,
  today,
} from '@/utils/format'
import type { Frequency, RecurringRule, TransactionType } from '@/types/api'
import '@/components/ui/page.css'

interface FormState {
  description: string
  amount: string
  type: TransactionType
  frequency: Frequency
  day_of_month: string
  weekday: string
  start_date: string
  end_date: string
  category_id: string
  account_id: string
}

function emptyForm(): FormState {
  return {
    description: '',
    amount: '',
    type: 'expense',
    frequency: 'monthly',
    day_of_month: '5',
    weekday: '0',
    start_date: today(),
    end_date: '',
    category_id: '',
    account_id: '',
  }
}

const WEEKDAYS = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']

export function RecurringPage() {
  const toast = useToast()
  const rules = useAsync(() => recurringApi.list(), [])
  const summary = useAsync(() => reportsApi.recurring(), [])
  const accounts = useAsync(() => accountsApi.list(), [])
  const categories = useAsync(() => categoriesApi.list(), [])
  const horizon = useAsync(
    () => recurringApi.occurrences(today(), addMonths(today(), 3)),
    [],
  )

  const [form, setForm] = useState<FormState>(emptyForm)
  const [editing, setEditing] = useState<RecurringRule | null>(null)
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [removing, setRemoving] = useState<RecurringRule | null>(null)

  const reloadAll = () => {
    rules.reload()
    summary.reload()
    horizon.reload()
  }

  const openCreate = () => {
    setForm(emptyForm())
    setEditing(null)
    setFormError(null)
    setOpen(true)
  }

  const openEdit = (rule: RecurringRule) => {
    setForm({
      description: rule.description,
      amount: rule.amount,
      type: rule.type,
      frequency: rule.frequency,
      day_of_month: String(rule.day_of_month ?? 1),
      weekday: String(rule.weekday ?? 0),
      start_date: rule.start_date,
      end_date: rule.end_date ?? '',
      category_id: rule.category_id ?? '',
      account_id: rule.account_id ?? '',
    })
    setEditing(rule)
    setFormError(null)
    setOpen(true)
  }

  const save = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setFormError(null)

    const payload = {
      description: form.description.trim(),
      amount: form.amount,
      type: form.type,
      frequency: form.frequency,
      day_of_month:
        form.frequency === 'monthly' || form.frequency === 'yearly'
          ? Number(form.day_of_month)
          : null,
      weekday: form.frequency === 'weekly' ? Number(form.weekday) : null,
      start_date: form.start_date,
      end_date: form.end_date || null,
      category_id: form.category_id || null,
      account_id: form.account_id || null,
    }

    try {
      if (editing) {
        await recurringApi.update(editing.id, payload)
        toast.success('Recorrência atualizada')
      } else {
        await recurringApi.create(payload)
        toast.success('Recorrência criada')
      }
      setOpen(false)
      reloadAll()
    } catch (cause) {
      setFormError(cause instanceof ApiError ? cause.message : 'Não foi possível salvar.')
    } finally {
      setSaving(false)
    }
  }

  const confirmOccurrence = async (ruleId: string, dueDate: string) => {
    try {
      await recurringApi.confirm(ruleId, dueDate)
      toast.success('Lançamento confirmado', 'A ocorrência virou uma transação.')
      reloadAll()
    } catch (cause) {
      toast.error('Não foi possível confirmar', cause instanceof ApiError ? cause.message : undefined)
    }
  }

  const confirmRemove = async () => {
    if (!removing) return
    try {
      await recurringApi.remove(removing.id)
      toast.success('Recorrência excluída')
    } catch (cause) {
      toast.error('Não foi possível excluir', cause instanceof ApiError ? cause.message : undefined)
    } finally {
      setRemoving(null)
      reloadAll()
    }
  }

  const pending = horizon.data?.filter((item) => !item.is_settled) ?? []

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">Contas recorrentes</h2>
          <p className="page__lede">O que se repete todo mês, previsto antes de acontecer.</p>
        </div>
        <GlassButton variant="primary" onClick={openCreate}>
          <Icon name="plus" size={16} />
          Nova recorrência
        </GlassButton>
      </div>

      {rules.error && <ErrorNotice detail={rules.error} />}

      <section className="grid grid--stats">
        <Stat
          label="Receitas recorrentes"
          value={formatMoney(summary.data?.recurring_income)}
          hint="Previstas para este mês"
          loading={summary.loading}
          tone="positive"
        />
        <Stat
          label="Despesas recorrentes"
          value={formatMoney(summary.data?.recurring_expenses)}
          hint="Previstas para este mês"
          loading={summary.loading}
          tone="negative"
        />
        <Stat
          label="Resultado previsto"
          value={formatMoney(summary.data?.net)}
          hint="Receitas menos despesas"
          loading={summary.loading}
        />
      </section>

      <section className="grid grid--split">
        <GlassCard title="Regras cadastradas" flush>
          {rules.loading ? (
            <div style={{ padding: 'var(--space-6)' }}>
              <Skeleton height={160} radius="var(--radius-md)" />
            </div>
          ) : (rules.data?.length ?? 0) === 0 ? (
            <EmptyState
              icon={<Icon name="repeat" size={28} />}
              title="Nenhuma recorrência"
              message="Cadastre aluguel, internet, salário — e o app passa a prever essas datas para você."
              action={<GlassButton onClick={openCreate}>Criar recorrência</GlassButton>}
            />
          ) : (
            <div className="record-list">
              {rules.data?.map((rule) => (
                <div key={rule.id} className="record">
                  <span
                    className="record__icon"
                    style={{
                      backgroundColor:
                        rule.type === 'income' ? 'var(--positive-soft)' : 'var(--negative-soft)',
                      color: rule.type === 'income' ? 'var(--positive)' : 'var(--negative)',
                    }}
                  >
                    <Icon name={rule.type === 'income' ? 'arrow-up' : 'arrow-down'} size={18} />
                  </span>
                  <div className="record__body">
                    <p className="record__title">{rule.description}</p>
                    <p className="record__meta">
                      {FREQUENCY_LABELS[rule.frequency]}
                      {rule.day_of_month && ` · todo dia ${rule.day_of_month}`}
                      {rule.weekday !== null &&
                        rule.frequency === 'weekly' &&
                        ` · toda ${WEEKDAYS[rule.weekday]?.toLowerCase()}`}
                    </p>
                  </div>
                  {!rule.is_active && <Badge>pausada</Badge>}
                  <span className="record__amount">{formatMoney(rule.amount)}</span>
                  <div className="record__actions">
                    <GlassButton
                      variant="ghost"
                      size="sm"
                      iconOnly
                      aria-label="Editar"
                      onClick={() => openEdit(rule)}
                    >
                      <Icon name="edit" size={15} />
                    </GlassButton>
                    <GlassButton
                      variant="ghost"
                      size="sm"
                      iconOnly
                      aria-label="Excluir"
                      onClick={() => setRemoving(rule)}
                    >
                      <Icon name="trash" size={15} />
                    </GlassButton>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        <GlassCard
          title="Próximas ocorrências"
          subtitle="Previsão para os próximos 3 meses"
          flush
        >
          {horizon.loading ? (
            <div style={{ padding: 'var(--space-6)' }}>
              <Skeleton height={160} radius="var(--radius-md)" />
            </div>
          ) : pending.length === 0 ? (
            <EmptyState
              compact
              icon={<Icon name="calendar" size={26} />}
              title="Nada previsto"
              message="As ocorrências aparecem aqui assim que você cadastrar uma regra."
            />
          ) : (
            <div className="record-list">
              {pending.slice(0, 10).map((occurrence) => (
                <div key={`${occurrence.rule_id}-${occurrence.due_date}`} className="record">
                  <div className="record__body">
                    <p className="record__title">{occurrence.description}</p>
                    <p className="record__meta">{formatRelativeDay(occurrence.due_date)}</p>
                  </div>
                  <span
                    className={`record__amount ${
                      occurrence.type === 'income' ? 'text-positive' : 'text-negative'
                    }`}
                  >
                    {formatMoney(occurrence.amount)}
                  </span>
                  <GlassButton
                    size="sm"
                    onClick={() => void confirmOccurrence(occurrence.rule_id, occurrence.due_date)}
                  >
                    Confirmar
                  </GlassButton>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </section>

      <GlassModal
        open={open}
        onClose={() => setOpen(false)}
        title={editing ? 'Editar recorrência' : 'Nova recorrência'}
        description="A previsão é calculada na hora. Nada vira transação até você confirmar."
        footer={
          <>
            <GlassButton variant="ghost" onClick={() => setOpen(false)}>
              Cancelar
            </GlassButton>
            <GlassButton variant="primary" form="recorrente-form" type="submit" loading={saving}>
              Salvar
            </GlassButton>
          </>
        }
      >
        <form id="recorrente-form" className="form-grid" onSubmit={save}>
          {formError && (
            <div className="form-grid__full">
              <ErrorNotice title="Verifique os dados" detail={formError} />
            </div>
          )}

          <GlassInput
            label="Descrição"
            value={form.description}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
            placeholder="Aluguel, internet, salário…"
            fieldClassName="form-grid__full"
            required
            autoFocus
          />

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

          <GlassSelect
            label="Tipo"
            value={form.type}
            onChange={(event) => setForm({ ...form, type: event.target.value as TransactionType })}
          >
            <option value="expense">Despesa</option>
            <option value="income">Receita</option>
          </GlassSelect>

          <GlassSelect
            label="Frequência"
            value={form.frequency}
            onChange={(event) => setForm({ ...form, frequency: event.target.value as Frequency })}
          >
            {Object.entries(FREQUENCY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </GlassSelect>

          {(form.frequency === 'monthly' || form.frequency === 'yearly') && (
            <GlassInput
              label="Dia do mês"
              type="number"
              min="1"
              max="31"
              value={form.day_of_month}
              onChange={(event) => setForm({ ...form, day_of_month: event.target.value })}
              hint="Dia 31 vira o último dia nos meses mais curtos."
            />
          )}

          {form.frequency === 'weekly' && (
            <GlassSelect
              label="Dia da semana"
              value={form.weekday}
              onChange={(event) => setForm({ ...form, weekday: event.target.value })}
            >
              {WEEKDAYS.map((label, index) => (
                <option key={label} value={index}>
                  {label}
                </option>
              ))}
            </GlassSelect>
          )}

          <GlassInput
            label="Começa em"
            type="date"
            value={form.start_date}
            onChange={(event) => setForm({ ...form, start_date: event.target.value })}
            required
          />

          <GlassInput
            label="Termina em"
            type="date"
            value={form.end_date}
            onChange={(event) => setForm({ ...form, end_date: event.target.value })}
            hint="Deixe vazio para não ter fim."
          />

          <GlassSelect
            label="Categoria"
            value={form.category_id}
            onChange={(event) => setForm({ ...form, category_id: event.target.value })}
          >
            <option value="">Sem categoria</option>
            {categories.data?.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </GlassSelect>

          <GlassSelect
            label="Conta"
            value={form.account_id}
            onChange={(event) => setForm({ ...form, account_id: event.target.value })}
          >
            <option value="">Nenhuma</option>
            {accounts.data?.accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.name}
              </option>
            ))}
          </GlassSelect>
        </form>
      </GlassModal>

      <ConfirmDialog
        open={removing !== null}
        title="Excluir recorrência"
        message={`A regra "${removing?.description}" deixará de gerar previsões. Os lançamentos já confirmados permanecem.`}
        confirmLabel="Excluir"
        destructive
        onConfirm={() => void confirmRemove()}
        onCancel={() => setRemoving(null)}
      />
    </div>
  )
}
