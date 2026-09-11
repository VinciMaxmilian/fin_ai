import { useState } from 'react'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassInput } from '@/components/ui/GlassInput'
import { ErrorNotice } from '@/components/ui/Feedback'
import { useToast } from '@/components/ui/Toast'
import { useAuth } from '@/stores/auth'
import './login.css'

type Mode = 'signin' | 'signup' | 'reset'

const COPY: Record<Mode, { title: string; lede: string; submit: string }> = {
  signin: {
    title: 'Entrar',
    lede: 'Sua vida financeira em um lugar só.',
    submit: 'Entrar',
  },
  signup: {
    title: 'Criar conta',
    lede: 'Leva menos de um minuto.',
    submit: 'Criar conta',
  },
  reset: {
    title: 'Recuperar senha',
    lede: 'Enviaremos um link para você definir uma nova senha.',
    submit: 'Enviar link',
  },
}

export function LoginPage() {
  const { signInWithPassword, signUp, signInWithGoogle, resetPassword } = useAuth()
  const toast = useToast()

  const [mode, setMode] = useState<Mode>('signin')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const copy = COPY[mode]

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      if (mode === 'signin') {
        await signInWithPassword(email, password)
      } else if (mode === 'signup') {
        const { needsConfirmation } = await signUp(email, password, fullName)
        if (needsConfirmation) {
          toast.info('Confirme seu e-mail', 'Enviamos um link para ativar a conta.')
          setMode('signin')
        }
      } else {
        await resetPassword(email)
        toast.success('Link enviado', 'Verifique sua caixa de entrada.')
        setMode('signin')
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível continuar.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleGoogle = async () => {
    setError(null)
    try {
      await signInWithGoogle()
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível continuar.')
    }
  }

  return (
    <div className="login">
      <div className="glass glass--level-3 login__panel">
        <div className="login__brand">
          <span className="login__logo" aria-hidden="true">
            F
          </span>
          <span className="login__wordmark">Fin</span>
        </div>

        <div>
          <h1 className="login__title">{copy.title}</h1>
          <p className="login__lede">{copy.lede}</p>
        </div>

        {error && <ErrorNotice title="Não foi possível continuar" detail={error} />}

        <form className="login__form" onSubmit={handleSubmit}>
          {mode === 'signup' && (
            <GlassInput
              label="Nome"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              autoComplete="name"
              placeholder="Como quer ser chamado"
              required
            />
          )}

          <GlassInput
            label="E-mail"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            placeholder="voce@email.com"
            required
          />

          {mode !== 'reset' && (
            <GlassInput
              label="Senha"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
              placeholder="••••••••"
              minLength={6}
              hint={mode === 'signup' ? 'Pelo menos 6 caracteres.' : undefined}
              required
            />
          )}

          <GlassButton type="submit" variant="primary" size="lg" block loading={submitting}>
            {copy.submit}
          </GlassButton>
        </form>

        {mode !== 'reset' && (
          <>
            <div className="login__divider">
              <span>ou</span>
            </div>

            <GlassButton variant="secondary" size="lg" block onClick={handleGoogle}>
              <GoogleMark />
              Continuar com Google
            </GlassButton>
          </>
        )}

        <div className="login__links">
          {mode === 'signin' && (
            <>
              <button type="button" onClick={() => setMode('signup')}>
                Criar uma conta
              </button>
              <button type="button" onClick={() => setMode('reset')}>
                Esqueci a senha
              </button>
            </>
          )}
          {mode !== 'signin' && (
            <button type="button" onClick={() => setMode('signin')}>
              Voltar para o login
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function GoogleMark() {
  return (
    <svg width="17" height="17" viewBox="0 0 18 18" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.92c1.7-1.57 2.68-3.88 2.68-6.62Z"
      />
      <path
        fill="#34A853"
        d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.92-2.26c-.8.54-1.84.86-3.04.86-2.34 0-4.32-1.58-5.03-3.7H.93v2.33A9 9 0 0 0 9 18Z"
      />
      <path
        fill="#FBBC05"
        d="M3.97 10.72a5.4 5.4 0 0 1 0-3.44V4.95H.93a9 9 0 0 0 0 8.1l3.04-2.33Z"
      />
      <path
        fill="#EA4335"
        d="M9 3.58c1.32 0 2.5.45 3.43 1.35l2.58-2.58C13.46.9 11.43 0 9 0A9 9 0 0 0 .93 4.95l3.04 2.33C4.68 5.16 6.66 3.58 9 3.58Z"
      />
    </svg>
  )
}
