import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from '@/services/supabase'
import { usersApi } from '@/services/endpoints'
import type { User } from '@/types/api'

interface AuthState {
  /** null = sem sessão. undefined nunca vaza: `loading` cobre a indefinição. */
  session: Session | null
  profile: User | null
  loading: boolean
  signInWithPassword: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, fullName: string) => Promise<{ needsConfirmation: boolean }>
  signInWithGoogle: () => Promise<void>
  resetPassword: (email: string) => Promise<void>
  signOut: () => Promise<void>
  refreshProfile: () => Promise<void>
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [profile, setProfile] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // O perfil local é criado pelo backend na primeira requisição autenticada,
  // então basta pedir /users/me depois que a sessão existe.
  const loadProfile = useCallback(async () => {
    try {
      setProfile(await usersApi.me())
    } catch {
      setProfile(null)
    }
  }, [])

  useEffect(() => {
    let active = true

    supabase.auth.getSession().then(({ data }) => {
      if (!active) return
      setSession(data.session)
      if (!data.session) setLoading(false)
    })

    const { data: subscription } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession)
      if (!nextSession) {
        setProfile(null)
        setLoading(false)
      }
    })

    return () => {
      active = false
      subscription.subscription.unsubscribe()
    }
  }, [])

  useEffect(() => {
    if (!session) return
    let active = true
    setLoading(true)
    loadProfile().finally(() => {
      if (active) setLoading(false)
    })
    return () => {
      active = false
    }
  }, [session, loadProfile])

  const value = useMemo<AuthState>(
    () => ({
      session,
      profile,
      loading,

      signInWithPassword: async (email, password) => {
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        if (error) throw new Error(translateAuthError(error.message))
      },

      signUp: async (email, password, fullName) => {
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { full_name: fullName } },
        })
        if (error) throw new Error(translateAuthError(error.message))
        // Sem sessão na resposta significa que o projeto exige confirmação
        // por email antes do primeiro login.
        return { needsConfirmation: !data.session }
      },

      signInWithGoogle: async () => {
        const { error } = await supabase.auth.signInWithOAuth({
          provider: 'google',
          options: { redirectTo: `${window.location.origin}/` },
        })
        if (error) throw new Error(translateAuthError(error.message))
      },

      resetPassword: async (email) => {
        const { error } = await supabase.auth.resetPasswordForEmail(email, {
          redirectTo: `${window.location.origin}/`,
        })
        if (error) throw new Error(translateAuthError(error.message))
      },

      signOut: async () => {
        await supabase.auth.signOut()
        setProfile(null)
      },

      refreshProfile: loadProfile,
    }),
    [session, profile, loading, loadProfile],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth precisa estar dentro de <AuthProvider>.')
  return context
}

/** As mensagens do Supabase vêm em inglês; as mais comuns ganham tradução. */
function translateAuthError(message: string): string {
  const map: Record<string, string> = {
    'Invalid login credentials': 'E-mail ou senha incorretos.',
    'Email not confirmed': 'Confirme seu e-mail antes de entrar.',
    'User already registered': 'Já existe uma conta com este e-mail.',
    'Password should be at least 6 characters':
      'A senha precisa ter pelo menos 6 caracteres.',
    'Unable to validate email address: invalid format': 'E-mail inválido.',
    'Signups not allowed for this instance': 'O cadastro está desativado no momento.',
  }

  for (const [english, portuguese] of Object.entries(map)) {
    if (message.includes(english)) return portuguese
  }

  if (message.includes('provider is not enabled')) {
    return 'Este método de login ainda não foi habilitado no projeto.'
  }

  return message
}
