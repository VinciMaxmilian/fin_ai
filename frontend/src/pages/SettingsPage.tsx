import { useState } from 'react'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassInput } from '@/components/ui/GlassInput'
import { ErrorNotice } from '@/components/ui/Feedback'
import { Icon } from '@/components/ui/Icon'
import { useToast } from '@/components/ui/Toast'
import { useAuth } from '@/stores/auth'
import { useTheme } from '@/hooks/useTheme'
import { usersApi } from '@/services/endpoints'
import { ApiError } from '@/services/client'
import { formatDate } from '@/utils/format'
import '@/components/ui/page.css'

export function SettingsPage() {
  const { profile, refreshProfile, signOut } = useAuth()
  const { theme, setTheme } = useTheme()
  const toast = useToast()

  const [fullName, setFullName] = useState(profile?.full_name ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const save = async (event: React.FormEvent) => {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await usersApi.update({ full_name: fullName.trim() || null })
      await refreshProfile()
      toast.success('Perfil atualizado')
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : 'Não foi possível salvar.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="page">
      <div className="page__intro">
        <div>
          <h2 className="page__greeting">Configurações</h2>
          <p className="page__lede">Seu perfil e as preferências do aplicativo.</p>
        </div>
      </div>

      <div className="grid grid--halves">
        <GlassCard title="Perfil">
          {error && <ErrorNotice title="Não foi possível salvar" detail={error} />}
          <form className="stack" style={{ gap: 'var(--space-4)' }} onSubmit={save}>
            <GlassInput
              label="Nome"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="Como quer ser chamado"
            />
            <GlassInput
              label="E-mail"
              value={profile?.email ?? ''}
              disabled
              hint="O e-mail é gerenciado pelo provedor de login."
            />
            <div>
              <GlassButton type="submit" variant="primary" loading={saving}>
                Salvar
              </GlassButton>
            </div>
          </form>
        </GlassCard>

        <div className="stack" style={{ gap: 'var(--space-5)' }}>
          <GlassCard title="Aparência">
            <div className="stack" style={{ gap: 'var(--space-3)' }}>
              <p className="text-secondary" style={{ fontSize: 'var(--text-sm)' }}>
                O tema escolhido fica salvo neste navegador.
              </p>
              <div className="row" style={{ gap: 'var(--space-2)' }}>
                <GlassButton
                  variant={theme === 'light' ? 'primary' : 'secondary'}
                  onClick={() => setTheme('light')}
                >
                  <Icon name="sun" size={16} />
                  Claro
                </GlassButton>
                <GlassButton
                  variant={theme === 'dark' ? 'primary' : 'secondary'}
                  onClick={() => setTheme('dark')}
                >
                  <Icon name="moon" size={16} />
                  Escuro
                </GlassButton>
              </div>
            </div>
          </GlassCard>

          <GlassCard title="Conta">
            <div className="stack" style={{ gap: 'var(--space-4)' }}>
              <div className="spread">
                <span className="text-secondary" style={{ fontSize: 'var(--text-sm)' }}>
                  Membro desde
                </span>
                <span style={{ fontSize: 'var(--text-sm)' }}>
                  {profile ? formatDate(profile.created_at.slice(0, 10)) : '—'}
                </span>
              </div>
              <div className="spread">
                <span className="text-secondary" style={{ fontSize: 'var(--text-sm)' }}>
                  Moeda
                </span>
                <span style={{ fontSize: 'var(--text-sm)' }}>{profile?.currency ?? 'BRL'}</span>
              </div>
              <div>
                <GlassButton onClick={() => void signOut()}>
                  <Icon name="logout" size={16} />
                  Sair da conta
                </GlassButton>
              </div>
            </div>
          </GlassCard>

          <GlassCard title="Privacidade">
            <p
              className="text-secondary"
              style={{ fontSize: 'var(--text-sm)', lineHeight: 'var(--leading-normal)' }}
            >
              Esta versão não acessa seu banco nem pede credenciais bancárias. Todos os saldos e
              lançamentos são informados por você, e seus dados ficam isolados dos demais usuários
              no servidor.
            </p>
          </GlassCard>
        </div>
      </div>
    </div>
  )
}
