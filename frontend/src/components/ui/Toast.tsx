import { createContext, useCallback, useContext, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { cx } from '@/utils/cx'
import './feedback.css'

type ToastTone = 'success' | 'error' | 'info'

interface Toast {
  id: number
  tone: ToastTone
  title: string
  message?: string
}

interface ToastApi {
  success: (title: string, message?: string) => void
  error: (title: string, message?: string) => void
  info: (title: string, message?: string) => void
}

const ToastContext = createContext<ToastApi | null>(null)

const DISMISS_AFTER_MS = 4500

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const nextId = useRef(1)

  const push = useCallback((tone: ToastTone, title: string, message?: string) => {
    const id = nextId.current++
    setToasts((current) => [...current, { id, tone, title, message }])
    window.setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id))
    }, DISMISS_AFTER_MS)
  }, [])

  const api = useMemo<ToastApi>(
    () => ({
      success: (title, message) => push('success', title, message),
      error: (title, message) => push('error', title, message),
      info: (title, message) => push('info', title, message),
    }),
    [push],
  )

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="toast-region" role="status" aria-live="polite">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={cx('glass', 'glass--level-3', 'toast', `toast--${toast.tone}`)}
          >
            <span className="toast__accent" />
            <div className="toast__body">
              <p className="toast__title">{toast.title}</p>
              {toast.message && <p className="toast__message">{toast.message}</p>}
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast(): ToastApi {
  const context = useContext(ToastContext)
  if (!context) {
    throw new Error('useToast precisa estar dentro de <ToastProvider>.')
  }
  return context
}
