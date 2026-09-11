import { getAccessToken, supabase } from './supabase'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

/** Erro vindo da API, já com a mensagem que pode ser mostrada ao usuário. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string = 'error',
    readonly details: unknown = null,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

type QueryValue = string | number | boolean | null | undefined

export type QueryParams = Record<string, QueryValue>

function buildUrl(path: string, params?: QueryParams): string {
  const url = new URL(BASE_URL + path)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null || value === '') continue
      url.searchParams.set(key, String(value))
    }
  }
  return url.toString()
}

/** Extrai a mensagem de erro em qualquer um dos formatos que a API devolve. */
async function readError(response: Response): Promise<ApiError> {
  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    return new ApiError(
      `Falha na comunicação com o servidor (${response.status}).`,
      response.status,
    )
  }

  const body = payload as {
    error?: { code?: string; message?: string; details?: unknown }
    detail?: unknown
  }

  // Formato próprio, vindo de AppError no backend.
  if (body?.error?.message) {
    return new ApiError(
      body.error.message,
      response.status,
      body.error.code ?? 'error',
      body.error.details,
    )
  }

  // Erro de validação do FastAPI: uma lista de problemas por campo.
  if (Array.isArray(body?.detail)) {
    const first = body.detail[0] as { msg?: string } | undefined
    const message = first?.msg?.replace(/^Value error,\s*/, '') ?? 'Dados inválidos.'
    return new ApiError(message, response.status, 'validation_error', body.detail)
  }

  if (typeof body?.detail === 'string') {
    return new ApiError(body.detail, response.status)
  }

  return new ApiError(`Erro inesperado (${response.status}).`, response.status)
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE'
  params?: QueryParams
  body?: unknown
  signal?: AbortSignal
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', params, body, signal } = options

  const token = await getAccessToken()
  const headers: Record<string, string> = { Accept: 'application/json' }
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  const response = await fetch(buildUrl(path, params), {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  })

  // O token expirou no meio do caminho: encerra a sessão para o app voltar
  // ao login em vez de ficar num limbo de requisições negadas.
  if (response.status === 401) {
    await supabase.auth.signOut()
    throw new ApiError('Sua sessão expirou. Entre novamente.', 401, 'unauthorized')
  }

  if (!response.ok) {
    throw await readError(response)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}

export const api = {
  get: <T>(path: string, params?: QueryParams, signal?: AbortSignal) =>
    request<T>(path, { params, signal }),
  post: <T>(path: string, body?: unknown, params?: QueryParams) =>
    request<T>(path, { method: 'POST', body, params }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PUT', body }),
  delete: (path: string) => request<void>(path, { method: 'DELETE' }),
}
