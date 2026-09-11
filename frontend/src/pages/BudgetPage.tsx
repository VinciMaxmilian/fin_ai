import { useState } from 'react'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassInput, GlassSelect } from '@/components/ui/GlassInput'
import { GlassModal } from '@/components/ui/GlassModal'
import { Badge, EmptyState, ErrorNotice, Progress, Skeleton } from '@/components/ui/Feedback'
import { Stat } from '@/components/ui/Stat'
import { Icon } from '@/components/ui/Icon'
import { useToast } from '@/components/ui/Toast'
import { useAsync } from '@/hooks/useAsync'
import { budgetsApi, categoriesApi } from '@/services/endpoints'
import { ApiError } from '@/services/client'
import {
  addMonths,
  firstDayOfMonth,
  formatMoney,
  formatMonth,
  formatPercent,
  toNumber,
} from '@/utils/format'
import '@/components/ui/page.css'

export function BudgetPage() {
  const toast = useToast()
  const [month, setMonth] = useState(firstDayOfMonth())
  const budget = useAsync(() => budgetsApi.summary(month), [month])
  const categories = useAsync(() => categoriesApi.list('expense'), [])

  const [open, setOpen] = useState(false)
  const [categoryId, setCategoryId] = useState('')
  const [amount, setAmount] = useState('')
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const save = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setFormError(null)
    try {
      await budgetsApi.set(month, categoryId, amount)
      toast.success('Orçamento definido')
      setOpen(false)
      setCategoryId('')
      setAmount('')
      budget.reload()
    } catch (cause) {
      setFormError(cause instanceof ApiError ? cause.message : 'Não foi possível salvar.')
    } finally {
      setSaving(false)
    }
  }

  const copyPrevious = async () => {
    try {
      await budgetsApi.copyPrevious(month)
      toast.success('Orçamento copiado', 'Os valores do mês anterior foram replicados.')
      budget.reload()
    } catch (cause) {
      toast.error('Não foi possível copiar', cause instanceof ApiError ? cause.message : undefined)
    }
  }

  const remove = async (id: string, name: string) => {
    try {
      await budgetsApi.remove(id)
      toast.success(`Orçamento de ${name} removido`)
      budget.reload()
    } catch (cause) {
      toast.error('Não foi possível remover', cause instanceof ApiError ? cause.message : undefined)
    }
  }

  const items = budget.data?.items ?? []
  const used = toNumber(budget.data?.used_percentage)

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">Orçamento</h2>
          <p className="page__lede">Quanto você planejou gastar, e quanto já gastou.</p>
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
            onClick={() => setMonth(addMonths(month, 1))}
          >
            <Icon name="chevron-right" size={15} />
          </GlassButton>
          <GlassButton variant="primary" onClick={() => setOpen(true)}>
            <Icon name="plus" size={16} />
            Definir
          </GlassButton>
        </div>
      </div>

      {budget.error && <ErrorNotice detail={budget.error} />}

      <section className="grid grid--stats">
        <Stat
          label="Planejado"
          value={formatMoney(budget.data?.total_planned)}
          loading={budget.loading}
        />
        <Stat
          label="Gasto"
          value={formatMoney(budget.data?.total_spent)}
          hint={`${formatPercent(used)} do planejado`}
          tone={used > 100 ? 'negative' : 'default'}
          loading={budget.loading}
        />
        <Stat
          label="Disponível"
          value={formatMoney(budget.data?.total_remaining)}
          tone={toNumber(budget.data?.total_remaining) < 0 ? 'negative' : 'positive'}
          loading={budget.loading}
        />
      </section>

      <GlassCard
        title="Por categoria"
        subtitle="Ordenado pelo que está mais próximo do limite"
        action={
          items.length === 0 ? undefined : (
            <GlassButton variant="ghost" size="sm" onClick={() => void copyPrevious()}>
              Copiar mês anterior
            </GlassButton>
          )
        }
      >
        {budget.loading ? (
          <Skeleton height={220} radius="var(--radius-md)" />
        ) : items.length === 0 ? (
          <EmptyState
            icon={<Icon name="budget" size={28} />}
            title="Nenhum limite definido"
            message="Escolha uma categoria e diga quanto pretende gastar nela neste mês."
            action={
              <div className="row" style={{ gap: 'var(--space-2)' }}>
                <GlassButton onClick={() => setOpen(true)}>Definir limite</GlassButton>
                <GlassButton variant="ghost" onClick={() => void copyPrevious()}>
                  Copiar mês anterior
                </GlassButton>
              </div>
            }
          />
        ) : (
          <div className="stack" style={{ gap: 'var(--space-6)' }}>
            {items.map((item) => {
              const percentage = toNumber(item.used_percentage)
              return (
                <div key={item.id} className="stack" style={{ gap: 'var(--space-2)' }}>
                  <div className="spread">
                    <span className="row" style={{ gap: 'var(--space-2)' }}>
                      <span
                        style={{
                          width: 9,
                          height: 9,
                          borderRadius: 3,
                          backgroundColor: item.category_color,
                        }}
                        aria-hidden="true"
                      />
                      <span style={{ fontWeight: 'var(--weight-medium)' }}>
                        {item.category_name}
                      </span>
                      {item.is_exceeded && <Badge tone="negative">estourou</Badge>}
                    </span>
                    <span className="row" style={{ gap: 'var(--space-3)' }}>
                      <span className="numeric" style={{ fontSize: 'var(--text-sm)' }}>
                        {formatMoney(item.spent)} de {formatMoney(item.amount)}
                      </span>
                      <GlassButton
                        variant="ghost"
                        size="sm"
                        iconOnly
                        aria-label={`Remover orçamento de ${item.category_name}`}
                        onClick={() => void remove(item.id, item.category_name)}
                      >
                        <Icon name="trash" size={14} />
                      </GlassButton>
                    </span>
                  </div>
                  <Progress
                    value={percentage}
                    color={item.is_exceeded ? 'var(--negative)' : item.category_color}
                    label={`${item.category_name}: ${formatPercent(percentage)} usado`}
                  />
                  <span className="text-tertiary" style={{ fontSize: 'var(--text-xs)' }}>
                    {item.is_exceeded
                      ? `${formatMoney(Math.abs(toNumber(item.remaining)))} acima do planejado`
                      : `${formatMoney(item.remaining)} disponíveis · ${formatPercent(percentage)} usado`}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </GlassCard>

      <GlassModal
        open={open}
        onClose={() => setOpen(false)}
        title="Definir limite"
        description={`Para ${formatMonth(month)}.`}
        footer={
          <>
            <GlassButton variant="ghost" onClick={() => setOpen(false)}>
              Cancelar
            </GlassButton>
            <GlassButton variant="primary" form="orcamento-form" type="submit" loading={saving}>
              Salvar
            </GlassButton>
          </>
        }
      >
        <form id="orcamento-form" className="form-grid" onSubmit={save}>
          {formError && (
            <div className="form-grid__full">
              <ErrorNotice title="Verifique os dados" detail={formError} />
            </div>
          )}

          <GlassSelect
            label="Categoria"
            value={categoryId}
            onChange={(event) => setCategoryId(event.target.value)}
            fieldClassName="form-grid__full"
            required
          >
            <option value="">Selecione</option>
            {categories.data?.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </GlassSelect>

          <GlassInput
            label="Limite do mês"
            type="number"
            step="0.01"
            min="0"
            prefix="R$"
            value={amount}
            onChange={(event) => setAmount(event.target.value)}
            fieldClassName="form-grid__full"
            hint="Definir de novo para a mesma categoria substitui o valor anterior."
            required
          />
        </form>
      </GlassModal>
    </div>
  )
}
