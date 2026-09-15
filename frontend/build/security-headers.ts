import type { Plugin } from 'vite'

/**
 * Gera o arquivo `_headers` do Netlify com os cabeçalhos de segurança.
 *
 * Por que gerar em vez de escrever à mão no `netlify.toml`: a diretiva
 * `connect-src` precisa listar exatamente para onde o app pode falar — a API e
 * o Supabase —, e essas URLs mudam por ambiente (local, preview, produção).
 * Uma CSP fixa no toml estaria errada em pelo menos um deles, e CSP errada
 * falha em silêncio: as requisições simplesmente não saem. Aqui ela é derivada
 * das mesmas variáveis que o bundle já usa, então nunca sai de sincronia.
 */

/** Extrai só a origem (esquema + host + porta), que é o que a CSP entende. */
function origin(url: string | undefined): string | null {
  if (!url) return null
  try {
    return new URL(url).origin
  } catch {
    return null
  }
}

export function buildCsp(apiUrl?: string, supabaseUrl?: string): string {
  const conecta = new Set<string>(["'self'"])

  for (const url of [apiUrl, supabaseUrl]) {
    const value = origin(url)
    if (value) conecta.add(value)
  }

  // O supabase-js abre um websocket se o app passar a usar realtime. Liberar a
  // origem equivalente agora evita uma quebra difícil de diagnosticar depois.
  const supabase = origin(supabaseUrl)
  if (supabase?.startsWith('https://')) {
    conecta.add(supabase.replace('https://', 'wss://'))
  }

  const tudoHttps = [...conecta]
    .filter((valor) => valor !== "'self'")
    .every((valor) => valor.startsWith('https://') || valor.startsWith('wss://'))

  return [
    // Nada carrega de lugar nenhum a menos que uma diretiva abaixo permita.
    "default-src 'self'",
    // Sem 'unsafe-inline' nem 'unsafe-eval': um script injetado não executa.
    // Esta é a linha que protege o token da sessão de um XSS.
    "script-src 'self'",
    // O app usa `style={{...}}` em vários componentes, e atributo de estilo
    // inline exige isto. Estilo não executa código: o risco é cosmético.
    "style-src 'self' 'unsafe-inline'",
    // Avatar do Google e logo de ativo vêm de domínios que não controlamos.
    // Imagem não executa, então liberar https: aqui é barato.
    "img-src 'self' data: https:",
    "font-src 'self'",
    `connect-src ${[...conecta].join(' ')}`,
    // Clickjacking: ninguém embute este app em um iframe.
    "frame-ancestors 'none'",
    "frame-src 'none'",
    "object-src 'none'",
    // Impede que uma injeção reescreva a base das URLs relativas.
    "base-uri 'self'",
    // Um formulário injetado não consegue postar credenciais para fora.
    "form-action 'self'",
    // Só quando tudo já é HTTPS. Com a API em http://localhost (build local,
    // Docker), esta diretiva reescreveria a URL para https e derrubaria todas
    // as chamadas — o remédio seria pior que a doença.
    ...(tudoHttps ? ['upgrade-insecure-requests'] : []),
  ].join('; ')
}

const CABECALHOS = (csp: string): Record<string, string> => ({
  'Content-Security-Policy': csp,
  // O navegador obedece ao content-type declarado em vez de adivinhá-lo.
  'X-Content-Type-Options': 'nosniff',
  // Redundante com frame-ancestors, para navegadores antigos.
  'X-Frame-Options': 'DENY',
  // Não vaza o caminho interno do app para sites de terceiros.
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=()',
  // Só HTTPS por 1 ano. O app não tem por que ser servido em texto claro.
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
})

export function securityHeaders(env: Record<string, string>): Plugin {
  return {
    name: 'gerar-cabecalhos-de-seguranca',
    apply: 'build',
    generateBundle() {
      const csp = buildCsp(env.VITE_API_URL, env.VITE_SUPABASE_URL)
      const linhas = Object.entries(CABECALHOS(csp)).map(
        ([nome, valor]) => `  ${nome}: ${valor}`,
      )

      // Formato do Netlify: um padrão de caminho, seguido dos cabeçalhos
      // indentados. `/*` cobre toda a aplicação.
      const conteudo = ['/*', ...linhas, ''].join('\n')

      this.emitFile({ type: 'asset', fileName: '_headers', source: conteudo })
    },
  }
}
