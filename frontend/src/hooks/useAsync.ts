import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from '@/services/client'

interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
  /** Recarrega ignorando o cache. Use depois de criar, editar ou excluir. */
  reload: () => void
}

/**
 * Carrega dados de forma assíncrona e devolve os três estados que a interface
 * precisa: carregando, erro e resultado.
 *
 * Bem mais simples que uma biblioteca de data fetching — e suficiente aqui,
 * porque as telas carregam sob demanda e não compartilham cache entre si.
 * Se um dia o app precisar de cache global, invalidação cruzada ou
 * revalidação em foco, este é o ponto para trocar por TanStack Query.
 *
 * `deps` funciona como o array de dependências do useEffect.
 */
export function useAsync<T>(
  loader: (signal: AbortSignal) => Promise<T>,
  deps: unknown[] = [],
): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [nonce, setNonce] = useState(0)

  // Guardado em ref para que mudar a função do loader a cada render não
  // dispare um recarregamento infinito.
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  useEffect(() => {
    const controller = new AbortController()
    let active = true

    setLoading(true)
    setError(null)

    loaderRef
      .current(controller.signal)
      .then((result) => {
        if (active) setData(result)
      })
      .catch((cause: unknown) => {
        if (!active || controller.signal.aborted) return
        if (cause instanceof DOMException && cause.name === 'AbortError') return
        setError(
          cause instanceof ApiError
            ? cause.message
            : 'Não foi possível carregar os dados. Verifique sua conexão.',
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
      controller.abort()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce])

  const reload = useCallback(() => setNonce((value) => value + 1), [])

  return { data, loading, error, reload }
}

/**
 * Envolve uma ação de escrita (criar, editar, excluir) e expõe se ela está em
 * andamento, para o botão poder mostrar o estado de carregando.
 */
export function useAction<Args extends unknown[], Result>(
  action: (...args: Args) => Promise<Result>,
) {
  const [running, setRunning] = useState(false)

  const run = useCallback(
    async (...args: Args): Promise<Result> => {
      setRunning(true)
      try {
        return await action(...args)
      } finally {
        setRunning(false)
      }
    },
    [action],
  )

  return { run, running }
}
