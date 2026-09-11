import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { GlassButton } from './GlassButton'
import { cx } from '@/utils/cx'
import './glass.css'

interface GlassModalProps {
  open: boolean
  onClose: () => void
  title: ReactNode
  description?: ReactNode
  /** Botões do rodapé. Sem eles, o rodapé não é renderizado. */
  footer?: ReactNode
  wide?: boolean
  children: ReactNode
}

export function GlassModal({
  open,
  onClose,
  title,
  description,
  footer,
  wide = false,
  children,
}: GlassModalProps) {
  const panelRef = useRef<HTMLDivElement>(null)

  // Esc fecha, e a rolagem do fundo trava enquanto o modal está aberto.
  useEffect(() => {
    if (!open) return

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', onKeyDown)

    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open, onClose])

  // Foco vai para o painel ao abrir, para o leitor de tela anunciar o diálogo.
  useEffect(() => {
    if (open) panelRef.current?.focus()
  }, [open])

  if (!open) return null

  return createPortal(
    <div
      className="glass-modal__backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div
        ref={panelRef}
        className={cx('glass', 'glass--level-3', 'glass-modal', wide && 'glass-modal--wide')}
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === 'string' ? title : undefined}
        tabIndex={-1}
      >
        <header className="glass-modal__header">
          <div>
            <h2 className="glass-modal__title">{title}</h2>
            {description && <p className="glass-modal__description">{description}</p>}
          </div>
          <GlassButton
            variant="ghost"
            size="sm"
            iconOnly
            onClick={onClose}
            aria-label="Fechar"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
              <path
                d="M1 1l12 12M13 1L1 13"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
            </svg>
          </GlassButton>
        </header>

        <div className="glass-modal__body">{children}</div>

        {footer && <footer className="glass-modal__footer">{footer}</footer>}
      </div>
    </div>,
    document.body,
  )
}

interface ConfirmDialogProps {
  open: boolean
  title: ReactNode
  /** Diga o que vai acontecer, não apenas "tem certeza?". */
  message: ReactNode
  confirmLabel?: string
  cancelLabel?: string
  destructive?: boolean
  loading?: boolean
  onConfirm: () => void
  onCancel: () => void
}

/** Confirmação para ações que não dá para desfazer. */
export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  destructive = false,
  loading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <GlassModal
      open={open}
      onClose={onCancel}
      title={title}
      footer={
        <>
          <GlassButton variant="ghost" onClick={onCancel} disabled={loading}>
            {cancelLabel}
          </GlassButton>
          <GlassButton
            variant={destructive ? 'danger' : 'primary'}
            onClick={onConfirm}
            loading={loading}
          >
            {confirmLabel}
          </GlassButton>
        </>
      }
    >
      <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--text-base)' }}>{message}</p>
    </GlassModal>
  )
}
