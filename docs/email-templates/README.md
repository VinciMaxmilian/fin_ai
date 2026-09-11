# Templates de e-mail do Supabase Auth

Os e-mails que o Supabase envia (confirmação, recuperação de senha, link mágico,
troca de endereço) usam um template padrão genérico. Estes arquivos substituem
por um visual alinhado ao app.

## Arquivos

| Arquivo | Onde colar no painel |
|---|---|
| `confirmacao.html` | Authentication → Emails → **Confirm signup** |
| `recuperar-senha.html` | Authentication → Emails → **Reset password** |
| `link-magico.html` | Authentication → Emails → **Magic Link** |
| `trocar-email.html` | Authentication → Emails → **Change Email Address** |

**Não edite os `.html` à mão** — eles são gerados. O design mora em `gerar.py`, e
só ali; cada template define apenas título, texto e rótulo do botão.

```bash
python docs/email-templates/gerar.py
```

## Como aplicar

1. Abra o painel do Supabase → **Authentication** → **Emails**.
2. Escolha o template na lista.
3. Cole o conteúdo do arquivo correspondente no campo de mensagem.
4. Ajuste o assunto. Sugestões:
   - Confirm signup — `Confirme seu e-mail`
   - Reset password — `Redefinir sua senha`
   - Magic Link — `Seu link de acesso ao Fin`
   - Change Email — `Confirme seu novo e-mail`
5. Salve e teste criando uma conta.

## Por que o HTML parece antiquado

Cliente de e-mail não é navegador. As escolhas abaixo são obrigatórias, não
preferência:

- **Layout em `<table>`** — o Outlook para desktop renderiza com o motor do
  Word, que não implementa flexbox nem grid.
- **CSS inline** — o Gmail descarta `<style>` em várias situações (e-mail
  encaminhado, versão web em certos modos).
- **Sem `backdrop-filter`, variáveis CSS ou blur** — nenhum cliente suporta.
  Por isso o glassmorphism do app **não** transfere literalmente. O que
  transfere é a linguagem: paleta neutra, cantos arredondados, bastante espaço
  negativo e tipografia limpa.
- **Botão com o padding no `<td>`, não no `<a>`** — um `<a>` sozinho perde a
  área de clique no Outlook; só o texto fica clicável.
- **Largura máxima de 520 px** — acima disso, quebra em vários clientes.

## Tema escuro

O bloco `@media (prefers-color-scheme: dark)` funciona no Apple Mail e em alguns
clientes. **O Gmail ignora** — e tudo bem: o tema claro é o padrão e se sustenta
sozinho. Nunca defina uma cor apenas dentro do bloco escuro.

## Variáveis disponíveis

| Variável | Conteúdo |
|---|---|
| `{{ .ConfirmationURL }}` | Link da ação |
| `{{ .Token }}` | Código de 6 dígitos |
| `{{ .TokenHash }}` | Hash do token, para montar uma URL própria |
| `{{ .Email }}` | E-mail do destinatário |
| `{{ .SiteURL }}` | URL do site configurada no projeto |
| `{{ .RedirectTo }}` | Destino após a confirmação |

## O remetente ainda é do Supabase

Mesmo com o template trocado, o e-mail chega como:

```
Supabase Auth <noreply@mail.app.supabase.io>
```

Isso é o que mais destoa de um produto próprio, e o template não resolve — é o
SMTP padrão do Supabase. Para o e-mail sair como **Fin**, configure SMTP próprio
em **Project Settings → Authentication → SMTP Settings**, com Resend, Postmark,
SendGrid, Amazon SES ou similar.

Além da aparência, o SMTP padrão tem limite baixo de envio (poucos e-mails por
hora) e é explicitamente marcado pelo Supabase como impróprio para produção.

## Testando o visual

Os arquivos são HTML comum: abra no navegador para ver o resultado. Para uma
prévia fiel, substitua as variáveis por valores de exemplo — e, para ver como o
Gmail renderiza, remova o bloco `@media (prefers-color-scheme: dark)`, que é
exatamente o que ele faz.
