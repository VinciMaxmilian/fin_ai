import './project-credit.css'

const SITE = 'https://atmosintelli.com.br/'

/**
 * Assinatura do projeto. Aparece no rodapé da sidebar (acima da conta) e na
 * tela de login, logo abaixo do aviso de segurança.
 *
 * `rel="noopener noreferrer"` não é adorno: sem `noopener`, a página aberta
 * recebe uma referência a esta janela em `window.opener` e pode trocá-la por
 * uma tela de login falsa enquanto o usuário olha para a outra aba — o golpe
 * conhecido como tabnabbing.
 */
export function ProjectCredit({ variant = 'login' }: { variant?: 'login' | 'sidebar' }) {
  return (
    <a
      className={`project-credit project-credit--${variant}`}
      href={SITE}
      target="_blank"
      rel="noopener noreferrer"
      title="Projeto pessoal desenvolvido por vincimaximilian — ATMOS INTELLI™"
    >
      <span className="project-credit__lead">Projeto pessoal desenvolvido por</span>
      <span className="project-credit__author">
        vincimaximilian <span aria-hidden="true">·</span> ATMOS INTELLI™
      </span>
    </a>
  )
}
