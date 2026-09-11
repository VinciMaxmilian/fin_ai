import { useEffect, useRef, useState } from 'react'

/**
 * Largura atual de um elemento, para o SVG dos gráficos acompanhar o container
 * sem esticar o texto.
 *
 * Devolve a ref a ser aplicada no elemento e a largura em pixels. O observer é
 * desconectado ao desmontar — sem isso, cada gráfico deixaria um observer vivo.
 */
export function useElementWidth(initial = 720) {
  const ref = useRef<HTMLDivElement | null>(null)
  const [width, setWidth] = useState(initial)

  useEffect(() => {
    const element = ref.current
    if (!element) return

    const observer = new ResizeObserver(([entry]) => {
      if (entry) setWidth(entry.contentRect.width)
    })
    observer.observe(element)
    setWidth(element.clientWidth || initial)

    return () => observer.disconnect()
  }, [initial])

  return { ref, width }
}
