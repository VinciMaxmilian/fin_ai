import { Icon } from './Icon'
import './security-notice.css'

/**
 * Selo discreto de segurança.
 *
 * Aparece na tela de login e no rodapé das páginas internas. O texto é
 * deliberadamente curto e verificável — descreve o que o app realmente faz
 * (conexão cifrada e dados isolados por conta), sem promessas de certificação
 * que não temos. Ver docs/seguranca.md para o que sustenta cada afirmação.
 */
export function SecurityNotice({ variant = 'inline' }: { variant?: 'inline' | 'footer' }) {
  return (
    <p className={`security-notice security-notice--${variant}`}>
      <Icon name="shield" size={14} className="security-notice__icon" />
      <span>
        Conexão criptografada. Seus dados são privados e visíveis apenas por você.
      </span>
    </p>
  )
}
