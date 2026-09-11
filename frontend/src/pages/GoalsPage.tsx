import { useState } from 'react'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassInput, GlassTextarea } from '@/components/ui/GlassInput'
import { GlassModal, ConfirmDialog } from '@/components/ui/GlassModal'
import { Badge, EmptyState, ErrorNotice, Progress, Skeleton } from '@/components/ui/Feedback'
import { Icon } from '@/components/ui/Icon'
import { useToast } from '@/components/ui/Toast'
import { useAsync } from '@/hooks/useAsync'
import { goalsApi } from '@/services/endpoints'
import { ApiError } from '@/services/client'
import { formatDate, formatMoney, formatPercent, toNumber } from '@/utils/format'
import { CATEGORICAL } from '@/components/charts/palette'
import type { Goal } from '@/types/api'
import '@/components/ui/page.css'

interface FormState {
  name: string
  target_amount: string
  current_amount: string
  target_date: string
  color: string
  notes: string
}

const EMPTY: FormState = {
  name: '',
  target_amount: '',
  current_amount: '0',
  target_date: '',
  color: CATEGORICAL[5]!.light,
  notes: '',
}

export function GoalsPage() {
  const toast = useToast()
  const { data, loading, error, reload } = useAsync(() => goalsApi.list(), [])

  const [form, setForm] = useState<FormState>(EMPTY)
  const [editing, setEditing] = useState<Goal | null>(null)
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [removing, setRemoving] = useState<Goal | null>(null)
  const [contributing, setContributing] = useState<Goal | null>(null)
  const [contribution, setContribution] = useState('')

  const openCreate = () => {
    setForm(EMPTY)
    setEditing(null)
    setFormError(null)
    setOpen(true)
  }

  const openEdit = (goal: Goal) => {
    setForm({
      name: goal.name,
      target_amount: goal.target_amount,
      current_amount: goal.current_amount,
      target_date: goal.target_date ?? '',
      color: goal.color,
      notes: goal.notes ?? '',
    })
    setEditing(goal)
    setFormError(null)
    setOpen(true)
  }

  const save = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setFormError(null)

    const payload = {
      name: form.name.trim(),
      target_amount: form.target_amount,
      current_amount: form.current_amount || '0',
      target_date: form.target_date || null,
      color: form.color,
      notes: form.notes.trim() || null,
    }

    try {
      if (editing) {
        await goalsApi.update(editing.id, payload)
        toast.success('Meta atualizada')
      } else {
        await goalsApi.create(payload)
        toast.success('Meta criada')
      }
      setOpen(false)
      reload()
    } catch (cause) {
      setFormError(cause instanceof ApiError ? cause.message : 'Não foi possível salvar.')
    } finally {
      setSaving(false)
    }
  }

  const saveContribution = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!contributing) return
    try {
      await goalsApi.contribute(contributing.id, contribution)
      toast.success('Aporte registrado')
      setContributing(null)
      setContribution('')
      reload()
    } catch (cause) {
      toast.error('Não foi possível registrar', cause instanceof ApiError ? cause.message : undefined)
    }
  }

  const confirmRemove = async () => {
    if (!removing) return
    try {
      await goalsApi.remove(removing.id)
      toast.success('Meta excluída')
    } catch (cause) {
      toast.error('Não foi possível excluir', cause instanceof ApiError ? cause.message : undefined)
    } finally {
      setRemoving(null)
      reload()
    }
  }

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">Metas</h2>
          <p className="page__lede">Onde você quer chegar, e quanto falta.</p>
        </div>
        <GlassButton variant="primary" onClick={openCreate}>
          <Icon name="plus" size={16} />
          Nova meta
        </GlassButton>
      </div>

      {error && <ErrorNotice detail={error} />}

      {loading ? (
        <div className="grid grid--cards">
          <Skeleton height={176} radius="var(--radius-lg)" />
          <Skeleton height={176} radius="var(--radius-lg)" />
        </div>
      ) : (data?.length ?? 0) === 0 ? (
        <GlassCard>
          <EmptyState
            icon={<Icon name="target" size={28} />}
            title="Nenhuma meta ainda"
            message="Reserva de emergência, uma viagem, um computador — defina o valor e acompanhe o progresso."
            action={<GlassButton onClick={openCreate}>Criar primeira meta</GlassButton>}
          />
        </GlassCard>
      ) : (
        <div className="grid grid--cards">
          {data?.map((goal) => (
            <GlassCard key={goal.id} compact>
              <div className="stack" style={{ gap: 'var(--space-4)' }}>
                <div className="spread">
                  <span
                    className="record__icon"
                    style={{ backgroundColor: `${goal.color}1F`, color: goal.color }}
                  >
                    <Icon name="target" size={19} />
                  </span>
                  <div className="record__actions" style={{ opacity: 1 }}>
                    <GlassButton
                      variant="ghost"
                      size="sm"
                      iconOnly
                      aria-label="Editar"
                      onClick={() => openEdit(goal)}
                    >
                      <Icon name="edit" size={15} />
                    </GlassButton>
                    <GlassButton
                      variant="ghost"
                      size="sm"
                      iconOnly
                      aria-label="Excluir"
                      onClick={() => setRemoving(goal)}
                    >
                      <Icon name="trash" size={15} />
                    </GlassButton>
                  </div>
                </div>

                <div className="spread">
                  <p style={{ fontWeight: 'var(--weight-medium)' }}>{goal.name}</p>
                  {goal.is_completed && <Badge tone="positive">concluída</Badge>}
                </div>

                <div>
                  <p className="stat__value" style={{ fontSize: 'var(--text-xl)' }}>
                    {formatMoney(goal.current_amount)}
                  </p>
                  <p className="text-tertiary" style={{ fontSize: 'var(--text-xs)' }}>
                    de {formatMoney(goal.target_amount)}
                    {goal.target_date && ` · até ${formatDate(goal.target_date)}`}
                  </p>
                </div>

                <div className="stack" style={{ gap: 'var(--space-2)' }}>
                  <Progress
                    value={toNumber(goal.progress)}
                    color={goal.color}
                    label={`${goal.name}: ${formatPercent(goal.progress)}`}
                  />
                  <div className="spread" style={{ fontSize: 'var(--text-xs)' }}>
                    <span className="text-tertiary">{formatPercent(goal.progress)}</span>
                    <span className="text-tertiary">
                      {goal.is_completed
                        ? 'Objetivo alcançado'
                        : `faltam ${formatMoney(goal.remaining)}`}
                    </span>
                  </div>
                </div>

                <GlassButton
                  size="sm"
                  block
                  onClick={() => {
                    setContributing(goal)
                    setContribution('')
                  }}
                >
                  Registrar aporte
                </GlassButton>
              </div>
            </GlassCard>
          ))}
        </div>
      )}

      <GlassModal
        open={open}
        onClose={() => setOpen(false)}
        title={editing ? 'Editar meta' : 'Nova meta'}
        footer={
          <>
            <GlassButton variant="ghost" onClick={() => setOpen(false)}>
              Cancelar
            </GlassButton>
            <GlassButton variant="primary" form="meta-form" type="submit" loading={saving}>
              Salvar
            </GlassButton>
          </>
        }
      >
        <form id="meta-form" className="form-grid" onSubmit={save}>
          {formError && (
            <div className="form-grid__full">
              <ErrorNotice title="Verifique os dados" detail={formError} />
            </div>
          )}

          <GlassInput
            label="Nome"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            placeholder="Reserva de emergência"
            fieldClassName="form-grid__full"
            required
            autoFocus
          />

          <GlassInput
            label="Objetivo"
            type="number"
            step="0.01"
            min="0.01"
            prefix="R$"
            value={form.target_amount}
            onChange={(event) => setForm({ ...form, target_amount: event.target.value })}
            required
          />

          <GlassInput
            label="Já guardado"
            type="number"
            step="0.01"
            min="0"
            prefix="R$"
            value={form.current_amount}
            onChange={(event) => setForm({ ...form, current_amount: event.target.value })}
          />

          <GlassInput
            label="Prazo"
            type="date"
            value={form.target_date}
            onChange={(event) => setForm({ ...form, target_date: event.target.value })}
            hint="Opcional"
          />

          <GlassInput
            label="Cor"
            type="color"
            value={form.color}
            onChange={(event) => setForm({ ...form, color: event.target.value })}
          />

          <GlassTextarea
            label="Observação"
            value={form.notes}
            onChange={(event) => setForm({ ...form, notes: event.target.value })}
            fieldClassName="form-grid__full"
          />
        </form>
      </GlassModal>

      <GlassModal
        open={contributing !== null}
        onClose={() => setContributing(null)}
        title={`Aporte · ${contributing?.name ?? ''}`}
        description="Use um valor negativo para registrar um resgate."
        footer={
          <>
            <GlassButton variant="ghost" onClick={() => setContributing(null)}>
              Cancelar
            </GlassButton>
            <GlassButton variant="primary" form="aporte-form" type="submit">
              Registrar
            </GlassButton>
          </>
        }
      >
        <form id="aporte-form" onSubmit={saveContribution} style={{ paddingBottom: 'var(--space-3)' }}>
          <GlassInput
            label="Valor"
            type="number"
            step="0.01"
            prefix="R$"
            value={contribution}
            onChange={(event) => setContribution(event.target.value)}
            required
            autoFocus
          />
        </form>
      </GlassModal>

      <ConfirmDialog
        open={removing !== null}
        title="Excluir meta"
        message={`A meta "${removing?.name}" e o histórico de aportes serão removidos. Esta ação não pode ser desfeita.`}
        confirmLabel="Excluir"
        destructive
        onConfirm={() => void confirmRemove()}
        onCancel={() => setRemoving(null)}
      />
    </div>
  )
}
