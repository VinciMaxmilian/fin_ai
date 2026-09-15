import { useState } from 'react'
import { APP_NAME, APP_SYMBOL } from '@/brand'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassInput } from '@/components/ui/GlassInput'
import { ErrorNotice } from '@/components/ui/Feedback'
import { ProjectCredit } from '@/components/ui/ProjectCredit'
import { SecurityNotice } from '@/components/ui/SecurityNotice'
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
  const { signInWithPassword, signUp, resetPassword } = useAuth()
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

  return (
    <div className="login">
      <div className="glass glass--level-3 login__panel">
        <div className="login__brand">
          <span className="login__logo" aria-hidden="true">
            {APP_SYMBOL}
          </span>
          <span className="login__wordmark">{APP_NAME}</span>
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

        {/* Aviso e assinatura formam um bloco so: o `gap` do painel os
            separaria demais e eles pareceriam dois rodapes soltos. */}
        <div className="login__meta">
          <SecurityNotice />
          <ProjectCredit />
        </div>
      </div>
    </div>
  )
}
