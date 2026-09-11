import { useState } from 'react'
import { Link } from 'react-router-dom'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { ConfirmDialog } from '@/components/ui/GlassModal'
import { Badge, EmptyState, ErrorNotice, Progress, Skeleton } from '@/components/ui/Feedback'
import { Stat } from '@/components/ui/Stat'
import { Icon } from '@/components/ui/Icon'
import { useToast } from '@/components/ui/Toast'
import { useAsync } from '@/hooks/useAsync'
import { installmentsApi } from '@/services/endpoints'
import { ApiError } from '@/services/client'
import { formatDate, formatMoney, toNumber } from '@/utils/format'
import type { InstallmentPlan } from '@/types/api'
import '@/components/ui/page.css'

export function InstallmentsPage() {
  const toast = useToast()
  const { data, loading, error, reload } = useAsync(() => installmentsApi.list(), [])
  const [removing, setRemoving] = useState<InstallmentPlan | null>(null)

  const confirmRemove = async () => {
    if (!removing) return
    try {
      await installmentsApi.remove(removing.id)
      toast.success('Parcelamento excluído')
    } catch (cause) {
      toast.error('Não foi possível excluir', cause instanceof ApiError ? cause.message : undefined)
    } finally {
      setRemoving(null)
      reload()
    }
  }

  const open = data?.filter((plan) => !plan.is_completed) ?? []
  const finished = data?.filter((plan) => plan.is_completed) ?? []
  const remainingTotal = open.reduce((acc, plan) => acc + toNumber(plan.remaining_amount), 0)
  const monthlyLoad = open.reduce((acc, plan) => acc + toNumber(plan.installment_amount), 0)

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">Parcelamentos</h2>
          <p className="page__lede">Compras divididas e o que ainda está por vir.</p>
        </div>
        <Link to="/transacoes?novo=1">
          <GlassButton variant="primary">
            <Icon name="plus" size={16} />
            Nova compra parcelada
          </GlassButton>
        </Link>
      </div>

      {error && <ErrorNotice detail={error} />}

      <section className="grid grid--stats">
        <Stat
          label="Saldo devedor"
          value={formatMoney(remainingTotal)}
          hint="Somando as parcelas ainda não vencidas"
          loading={loading}
          large
        />
        <Stat
          label="Compromisso mensal"
          value={formatMoney(monthlyLoad)}
          hint={`${open.length} parcelamentos em aberto`}
          loading={loading}
        />
      </section>

      {loading ? (
        <Skeleton height={220} radius="var(--radius-lg)" />
      ) : (data?.length ?? 0) === 0 ? (
        <GlassCard>
          <EmptyState
            icon={<Icon name="installments" size={28} />}
            title="Nenhuma compra parcelada"
            message="Ao lançar uma despesa, informe o número de parcelas — o app cria uma transação para cada uma e reflete tudo nas faturas futuras."
            action={
              <Link to="/transacoes?novo=1">
                <GlassButton>Lançar compra parcelada</GlassButton>
              </Link>
            }
          />
        </GlassCard>
      ) : (
        <>
          {open.length > 0 && (
            <div className="grid grid--cards">
              {open.map((plan) => (
                <PlanCard key={plan.id} plan={plan} onRemove={() => setRemoving(plan)} />
              ))}
            </div>
          )}

          {finished.length > 0 && (
            <GlassCard title="Quitados" flush>
              <div className="record-list">
                {finished.map((plan) => (
                  <div key={plan.id} className="record">
                    <span
                      className="record__icon"
                      style={{ backgroundColor: 'var(--positive-soft)', color: 'var(--positive)' }}
                    >
                      <Icon name="check" size={18} />
                    </span>
                    <div className="record__body">
                      <p className="record__title">{plan.description}</p>
                      <p className="record__meta">
                        {plan.installments_count}x de {formatMoney(plan.installment_amount)}
                      </p>
                    </div>
                    <span className="record__amount">{formatMoney(plan.total_amount)}</span>
                    <div className="record__actions">
                      <GlassButton
                        variant="ghost"
                        size="sm"
                        iconOnly
                        aria-label="Excluir"
                        onClick={() => setRemoving(plan)}
                      >
                        <Icon name="trash" size={15} />
                      </GlassButton>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          )}
        </>
      )}

      <ConfirmDialog
        open={removing !== null}
        title="Excluir parcelamento"
        message={`Excluir "${removing?.description}" remove as ${removing?.installments_count ?? 0} parcelas, inclusive as já lançadas. Esta ação não pode ser desfeita.`}
        confirmLabel="Excluir tudo"
        destructive
        onConfirm={() => void confirmRemove()}
        onCancel={() => setRemoving(null)}
      />
    </div>
  )
}

function PlanCard({ plan, onRemove }: { plan: InstallmentPlan; onRemove: () => void }) {
  const progress = (plan.paid_installments / plan.installments_count) * 100

  return (
    <GlassCard compact>
      <div className="stack" style={{ gap: 'var(--space-4)' }}>
        <div className="spread">
          <span
            className="record__icon"
            style={{ backgroundColor: 'var(--info-soft)', color: 'var(--info)' }}
          >
            <Icon name="installments" size={19} />
          </span>
          <div className="record__actions" style={{ opacity: 1 }}>
            <GlassButton variant="ghost" size="sm" iconOnly aria-label="Excluir" onClick={onRemove}>
              <Icon name="trash" size={15} />
            </GlassButton>
          </div>
        </div>

        <div>
          <p style={{ fontWeight: 'var(--weight-medium)' }}>{plan.description}</p>
          <p className="text-tertiary" style={{ fontSize: 'var(--text-xs)' }}>
            {plan.installments_count}x de {formatMoney(plan.installment_amount)}
          </p>
        </div>

        <div className="spread">
          <div>
            <p className="text-secondary" style={{ fontSize: 'var(--text-xs)' }}>
              Restante
            </p>
            <p className="stat__value" style={{ fontSize: 'var(--text-lg)' }}>
              {formatMoney(plan.remaining_amount)}
            </p>
          </div>
          <Badge>
            {plan.paid_installments}/{plan.installments_count}
          </Badge>
        </div>

        <div className="stack" style={{ gap: 'var(--space-2)' }}>
          <Progress value={progress} label={`${plan.description}: progresso das parcelas`} />
          {plan.next_due_date && (
            <span className="text-tertiary" style={{ fontSize: 'var(--text-xs)' }}>
              Próxima parcela em {formatDate(plan.next_due_date)}
            </span>
          )}
        </div>
      </div>
    </GlassCard>
  )
}
