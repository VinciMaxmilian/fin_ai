import { useId } from 'react'
import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react'
import { cx } from '@/utils/cx'
import './glass.css'

interface FieldShellProps {
  label?: ReactNode
  error?: string | null
  hint?: ReactNode
  htmlFor: string
  className?: string
  children: ReactNode
}

/** Rótulo, erro e dica em volta de qualquer controle. */
function FieldShell({ label, error, hint, htmlFor, className, children }: FieldShellProps) {
  return (
    <div className={cx('glass-field', className)}>
      {label && (
        <label className="glass-field__label" htmlFor={htmlFor}>
          {label}
        </label>
      )}
      <div className="glass-field__control">{children}</div>
      {error ? (
        <span className="glass-field__error" role="alert">
          {error}
        </span>
      ) : (
        hint && <span className="glass-field__hint">{hint}</span>
      )}
    </div>
  )
}

interface GlassInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'prefix'> {
  label?: ReactNode
  error?: string | null
  hint?: ReactNode
  /** Texto fixo dentro do campo, à esquerda. Ex.: "R$". */
  prefix?: string
  fieldClassName?: string
}

export function GlassInput({
  label,
  error,
  hint,
  prefix,
  fieldClassName,
  className,
  id,
  ...rest
}: GlassInputProps) {
  const generatedId = useId()
  const inputId = id ?? generatedId

  return (
    <FieldShell
      label={label}
      error={error}
      hint={hint}
      htmlFor={inputId}
      className={fieldClassName}
    >
      {prefix && <span className="glass-field__prefix">{prefix}</span>}
      <input
        id={inputId}
        className={cx(
          'glass-input',
          prefix && 'glass-input--with-prefix',
          error && 'glass-input--invalid',
          className,
        )}
        aria-invalid={error ? true : undefined}
        {...rest}
      />
    </FieldShell>
  )
}

interface GlassSelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: ReactNode
  error?: string | null
  hint?: ReactNode
  fieldClassName?: string
}

export function GlassSelect({
  label,
  error,
  hint,
  fieldClassName,
  className,
  id,
  children,
  ...rest
}: GlassSelectProps) {
  const generatedId = useId()
  const selectId = id ?? generatedId

  return (
    <FieldShell
      label={label}
      error={error}
      hint={hint}
      htmlFor={selectId}
      className={fieldClassName}
    >
      <select
        id={selectId}
        className={cx('glass-input', error && 'glass-input--invalid', className)}
        aria-invalid={error ? true : undefined}
        {...rest}
      >
        {children}
      </select>
    </FieldShell>
  )
}

interface GlassTextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: ReactNode
  error?: string | null
  hint?: ReactNode
  fieldClassName?: string
}

export function GlassTextarea({
  label,
  error,
  hint,
  fieldClassName,
  className,
  id,
  ...rest
}: GlassTextareaProps) {
  const generatedId = useId()
  const textareaId = id ?? generatedId

  return (
    <FieldShell
      label={label}
      error={error}
      hint={hint}
      htmlFor={textareaId}
      className={fieldClassName}
    >
      <textarea
        id={textareaId}
        className={cx('glass-input', error && 'glass-input--invalid', className)}
        aria-invalid={error ? true : undefined}
        {...rest}
      />
    </FieldShell>
  )
}
