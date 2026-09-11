import { useState } from 'react'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassInput, GlassSelect } from '@/components/ui/GlassInput'
import { GlassModal, ConfirmDialog } from '@/components/ui/GlassModal'
import { Badge, EmptyState, ErrorNotice, Skeleton } from '@/components/ui/Feedback'
import { Icon, iconOf } from '@/components/ui/Icon'
import { useToast } from '@/components/ui/Toast'
import { useAsync } from '@/hooks/useAsync'
import { categoriesApi } from '@/services/endpoints'
import { ApiError } from '@/services/client'
import { CATEGORICAL, MUTED_SLOT } from '@/components/charts/palette'
import type { Category, CategoryKind } from '@/types/api'
import '@/components/ui/page.css'

const KIND_LABELS: Record<CategoryKind, string> = {
  expense: 'Despesa',
  income: 'Receita',
  both: 'Ambos',
}

const ICON_OPTIONS = [
  'tag', 'home', 'utensils', 'car', 'heart', 'book', 'sparkles',
  'bag', 'plane', 'repeat', 'trending-up', 'wallet',
] as const

/** Só as cores validadas para gráfico são oferecidas. */
const COLOR_OPTIONS = [...CATEGORICAL.map((slot) => slot.light), MUTED_SLOT.light]

interface FormState {
  name: string
  kind: CategoryKind
  color: string
  icon: string
}

const EMPTY: FormState = { name: '', kind: 'expense', color: CATEGORICAL[0]!.light, icon: 'tag' }

export function CategoriesPage() {
  const toast = useToast()
  const { data, loading, error, reload } = useAsync(() => categoriesApi.list(), [])

  const [form, setForm] = useState<FormState>(EMPTY)
  const [editing, setEditing] = useState<Category | null>(null)
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [removing, setRemoving] = useState<Category | null>(null)

  const openCreate = () => {
    setForm(EMPTY)
    setEditing(null)
    setFormError(null)
    setOpen(true)
  }

  const openEdit = (category: Category) => {
    setForm({
      name: category.name,
      kind: category.kind,
      color: category.color,
      icon: category.icon,
    })
    setEditing(category)
    setFormError(null)
    setOpen(true)
  }

  const save = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setFormError(null)

    const payload = {
      name: form.name.trim(),
      kind: form.kind,
      color: form.color,
      icon: form.icon,
    }

    try {
      if (editing) {
        await categoriesApi.update(editing.id, payload)
        toast.success('Categoria atualizada')
      } else {
        await categoriesApi.create(payload)
        toast.success('Categoria criada')
      }
      setOpen(false)
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
      await categoriesApi.remove(removing.id)
      toast.success('Categoria excluída')
    } catch (cause) {
      toast.error('Não foi possível excluir', cause instanceof ApiError ? cause.message : undefined)
    } finally {
      setRemoving(null)
      reload()
    }
  }

  const expenses = data?.filter((item) => item.kind === 'expense') ?? []
  const incomes = data?.filter((item) => item.kind === 'income') ?? []
  const both = data?.filter((item) => item.kind === 'both') ?? []

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">Categorias</h2>
          <p className="page__lede">Como seus gastos são organizados.</p>
        </div>
        <GlassButton variant="primary" onClick={openCreate}>
          <Icon name="plus" size={16} />
          Nova categoria
        </GlassButton>
      </div>

      {error && <ErrorNotice detail={error} />}

      {loading ? (
        <Skeleton height={280} radius="var(--radius-lg)" />
      ) : (data?.length ?? 0) === 0 ? (
        <GlassCard>
          <EmptyState
            icon={<Icon name="tag" size={28} />}
            title="Nenhuma categoria"
            message="Crie categorias para agrupar seus lançamentos."
            action={<GlassButton onClick={openCreate}>Criar categoria</GlassButton>}
          />
        </GlassCard>
      ) : (
        <div className="grid grid--halves">
          <CategoryGroup title="Despesas" items={expenses} onEdit={openEdit} onRemove={setRemoving} />
          <div className="stack" style={{ gap: 'var(--space-5)' }}>
            <CategoryGroup title="Receitas" items={incomes} onEdit={openEdit} onRemove={setRemoving} />
            <CategoryGroup
              title="Receitas e despesas"
              items={both}
              onEdit={openEdit}
              onRemove={setRemoving}
            />
          </div>
        </div>
      )}

      <GlassModal
        open={open}
        onClose={() => setOpen(false)}
        title={editing ? 'Editar categoria' : 'Nova categoria'}
        footer={
          <>
            <GlassButton variant="ghost" onClick={() => setOpen(false)}>
              Cancelar
            </GlassButton>
            <GlassButton variant="primary" form="categoria-form" type="submit" loading={saving}>
              Salvar
            </GlassButton>
          </>
        }
      >
        <form id="categoria-form" className="form-grid" onSubmit={save}>
          {formError && (
            <div className="form-grid__full">
              <ErrorNotice title="Verifique os dados" detail={formError} />
            </div>
          )}

          <GlassInput
            label="Nome"
            value={form.name}
            onChange={(event) => setForm({ ...form, name: event.target.value })}
            fieldClassName="form-grid__full"
            required
            autoFocus
          />

          <GlassSelect
            label="Usar em"
            value={form.kind}
            onChange={(event) => setForm({ ...form, kind: event.target.value as CategoryKind })}
          >
            {Object.entries(KIND_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </GlassSelect>

          <GlassSelect
            label="Ícone"
            value={form.icon}
            onChange={(event) => setForm({ ...form, icon: event.target.value })}
          >
            {ICON_OPTIONS.map((icon) => (
              <option key={icon} value={icon}>
                {icon}
              </option>
            ))}
          </GlassSelect>

          <div className="glass-field form-grid__full">
            <span className="glass-field__label">Cor</span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
              {COLOR_OPTIONS.map((color) => (
                <button
                  key={color}
                  type="button"
                  aria-label={`Cor ${color}`}
                  aria-pressed={form.color.toUpperCase() === color.toUpperCase()}
                  onClick={() => setForm({ ...form, color })}
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: 'var(--radius-xs)',
                    backgroundColor: color,
                    outline:
                      form.color.toUpperCase() === color.toUpperCase()
                        ? '2px solid var(--text-primary)'
                        : 'none',
                    outlineOffset: 2,
                  }}
                />
              ))}
            </div>
            <span className="glass-field__hint">
              Cores escolhidas para continuarem distinguíveis nos gráficos, inclusive por quem
              tem daltonismo.
            </span>
          </div>
        </form>
      </GlassModal>

      <ConfirmDialog
        open={removing !== null}
        title="Excluir categoria"
        message={`A categoria "${removing?.name}" será removida. Categorias em uso por lançamentos precisam ser recategorizadas antes.`}
        confirmLabel="Excluir"
        destructive
        onConfirm={() => void confirmRemove()}
        onCancel={() => setRemoving(null)}
      />
    </div>
  )
}

function CategoryGroup({
  title,
  items,
  onEdit,
  onRemove,
}: {
  title: string
  items: Category[]
  onEdit: (category: Category) => void
  onRemove: (category: Category) => void
}) {
  if (items.length === 0) return null

  return (
    <GlassCard title={title} subtitle={`${items.length} categorias`} flush>
      <div className="record-list">
        {items.map((category) => (
          <div key={category.id} className="record">
            <span
              className="record__icon"
              style={{ backgroundColor: `${category.color}1F`, color: category.color }}
            >
              <Icon name={iconOf(category.icon)} size={18} />
            </span>
            <div className="record__body">
              <p className="record__title">{category.name}</p>
            </div>
            {category.is_system && <Badge>padrão</Badge>}
            <div className="record__actions">
              <GlassButton
                variant="ghost"
                size="sm"
                iconOnly
                aria-label="Editar"
                onClick={() => onEdit(category)}
              >
                <Icon name="edit" size={15} />
              </GlassButton>
              {!category.is_system && (
                <GlassButton
                  variant="ghost"
                  size="sm"
                  iconOnly
                  aria-label="Excluir"
                  onClick={() => onRemove(category)}
                >
                  <Icon name="trash" size={15} />
                </GlassButton>
              )}
            </div>
          </div>
        ))}
      </div>
    </GlassCard>
  )
}
