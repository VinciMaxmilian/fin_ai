import { createClient } from '@supabase/supabase-js'

/**
 * Cliente do Supabase Auth.
 *
 * Só cuida de identidade: login, cadastro, OAuth e renovação do token. Nenhum
 * dado financeiro passa por aqui — isso é responsabilidade do FastAPI, para
 * que web, iOS e Android compartilhem as mesmas regras de negócio.
 *
 * A chave usada é a publicável (anon), feita para ficar exposta no cliente. O
 * schema `public` está com RLS ligada e sem GRANT para as roles anon e
 * authenticated, então esta chave não abre as tabelas do app.
 */

const url = import.meta.env.VITE_SUPABASE_URL
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!url || !anonKey) {
  throw new Error(
    'Configure VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY no .env da raiz do projeto.',
  )
}

export const supabase = createClient(url, anonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
    flowType: 'pkce',
  },
})

export async function getAccessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token ?? null
}
