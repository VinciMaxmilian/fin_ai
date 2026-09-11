import { useEffect, useId, useRef, useState } from 'react'
import { GlassInput } from '@/components/ui/GlassInput'
import { Icon } from '@/components/ui/Icon'
import { useDebounced } from '@/hooks/useDebounced'
import { marketApi } from '@/services/endpoints'
import { formatMoney } from '@/utils/format'
import type { AssetSearchResult, Quote } from '@/types/api'
import './ticker-field.css'

interface TickerFieldProps {
  value: string
  onChange: (ticker: string) => void
  /** Chamado quando uma cotação é encontrada, para preencher o preço atual. */
  onQuote?: (quote: Quote | null) => void
  disabled?: boolean
  hint?: string
}

/**
 * Campo de código de negociação com sugestões e cotação ao vivo.
 *
 * A busca e a cotação passam pelo nosso backend — o token da brapi é segredo de
 * servidor e nunca chega ao navegador.
 */
export function TickerField({ value, onChange, onQuote, disabled, hint }: TickerFieldProps) {
  const listId = useId()
  const [suggestions, setSuggestions] = useState<AssetSearchResult[]>([])
  const [quote, setQuote] = useState<Quote | null>(null)
  const [loadingQuote, setLoadingQuote] = useState(false)
  const [quoteError, setQuoteError] = useState<string | null>(null)
  const [open, setOpen] = useState(false)

  const debounced = useDebounced(value.trim().toUpperCase(), 350)
  // Guardado em ref para o efeito não reagir a uma função nova a cada render.
  const onQuoteRef = useRef(onQuote)
  onQuoteRef.current = onQuote

  // Sugestões de código enquanto digita.
  useEffect(() => {
    if (debounced.length < 2) {
      setSuggestions([])
      return
    }
    const controller = new AbortController()
    marketApi
      .search(debounced, controller.signal)
      .then((results) => setSuggestions(results.slice(0, 8)))
      .catch(() => setSuggestions([]))
    return () => controller.abort()
  }, [debounced])

  // Cotação do código completo.
  useEffect(() => {
    if (debounced.length < 4) {
      setQuote(null)
      setQuoteError(null)
      onQuoteRef.current?.(null)
      return
    }

    let active = true
    setLoadingQuote(true)
    setQuoteError(null)

    marketApi
      .quote(debounced)
      .then((result) => {
        if (!active) return
        setQuote(result)
        onQuoteRef.current?.(result)
      })
      .catch(() => {
        if (!active) return
        setQuote(null)
        setQuoteError('Sem cotação para este código.')
        onQuoteRef.current?.(null)
      })
      .finally(() => {
        if (active) setLoadingQuote(false)
      })

    return () => {
      active = false
    }
  }, [debounced])

  return (
    <div className="ticker-field">
      <GlassInput
        label="Código"
        value={value}
        onChange={(event) => onChange(event.target.value.toUpperCase())}
        onFocus={() => setOpen(true)}
        // Atraso para o clique na sugestão acontecer antes do fechamento.
        onBlur={() => window.setTimeout(() => setOpen(false), 150)}
        placeholder="PETR4, HGLG11, IVVB11…"
        autoComplete="off"
        spellCheck={false}
        disabled={disabled}
        list={undefined}
        aria-describedby={listId}
        hint={hint ?? 'Deixe vazio para informar o preço manualmente.'}
      />

      {open && suggestions.length > 0 && (
        <ul className="ticker-field__suggestions" id={listId}>
          {suggestions.map((item) => (
            <li key={item.symbol}>
              <button
                type="button"
                onMouseDown={(event) => {
                  // mousedown roda antes do blur: garante a seleção.
                  event.preventDefault()
                  onChange(item.symbol)
                  setOpen(false)
                }}
              >
                <span className="ticker-field__symbol">{item.symbol}</span>
                <span className="ticker-field__kind">{item.kind}</span>
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="ticker-field__status" aria-live="polite">
        {loadingQuote && <span className="text-tertiary">Buscando cotação…</span>}

        {!loadingQuote && quote && (
          <span className="ticker-field__quote">
            <Icon name="check" size={13} style={{ color: 'var(--positive)' }} />
            <strong>{formatMoney(quote.price)}</strong>
            {quote.change_percent && (
              <span
                className={Number(quote.change_percent) >= 0 ? 'text-positive' : 'text-negative'}
              >
                {Number(quote.change_percent) >= 0 ? '+' : ''}
                {quote.change_percent}%
              </span>
            )}
            {quote.long_name && <span className="text-tertiary">{quote.long_name}</span>}
          </span>
        )}

        {!loadingQuote && quoteError && value.trim().length >= 4 && (
          <span className="text-tertiary">{quoteError}</span>
        )}
      </div>
    </div>
  )
}
