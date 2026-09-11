import { useEffect, useState } from 'react'

/**
 * Atrasa a propagação de um valor.
 *
 * Usado na busca de transações: sem isso, cada tecla dispararia uma requisição.
 */
export function useDebounced<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs)
    return () => window.clearTimeout(timer)
  }, [value, delayMs])

  return debounced
}
