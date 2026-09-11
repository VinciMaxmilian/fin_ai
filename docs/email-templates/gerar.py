"""Gera os templates de e-mail do Supabase Auth a partir de um esqueleto unico.

    python docs/email-templates/gerar.py

O design mora em `SHELL`, e so ali. Cada template define apenas titulo, texto e
rotulo do botao -- assim uma mudanca visual nao precisa ser repetida cinco
vezes, que e como templates de e-mail costumam sair do lugar.

Por que o HTML e "antiquado":
- layout em <table>, porque o Outlook usa o motor do Word e nao tem flex/grid;
- CSS inline, porque o Gmail descarta <style> em varias situacoes;
- sem backdrop-filter, variaveis CSS ou blur -- nenhum cliente de e-mail
  suporta. Do design do app, o que transfere e a linguagem: paleta neutra,
  cantos arredondados, bastante espaco e tipografia limpa.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SHELL = """<!--
  Fin — {titulo_arquivo} (Supabase Auth)

  Cole em: painel do Supabase → Authentication → Emails → {local}

  NAO EDITE ESTE ARQUIVO A MAO: ele e gerado por docs/email-templates/gerar.py.
  Mude o esqueleto la e rode o script de novo.
-->
<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="color-scheme" content="light dark" />
    <meta name="supported-color-schemes" content="light dark" />
    <title>{titulo}</title>
    <!--[if mso]>
      <style>
        body, table, td, p, a {{ font-family: 'Segoe UI', Arial, sans-serif !important; }}
      </style>
    <![endif]-->
    <style>
      /* Apple Mail respeita; o Gmail ignora, e tudo bem: o tema claro e o
         padrao e se sustenta sozinho. */
      @media (prefers-color-scheme: dark) {{
        .fin-bg {{ background-color: #0b0b0d !important; }}
        .fin-card {{ background-color: #1c1c1e !important; border-color: #2c2c2e !important; }}
        .fin-title, .fin-code {{ color: #f5f5f7 !important; }}
        .fin-text {{ color: #a1a1a8 !important; }}
        .fin-muted, .fin-footer {{ color: #75757c !important; }}
        .fin-button {{ background-color: #f5f5f7 !important; color: #1c1c1e !important; }}
        .fin-divider {{ border-color: #2c2c2e !important; }}
        .fin-codebox {{ background-color: #2c2c2e !important; border-color: #3a3a3c !important; }}
      }}

      @media only screen and (max-width: 600px) {{
        .fin-card {{ padding: 32px 24px !important; }}
        .fin-title {{ font-size: 24px !important; }}
      }}
    </style>
  </head>

  <body class="fin-bg" style="margin:0; padding:0; background-color:#f2f2f7; -webkit-font-smoothing:antialiased;">
    <div style="display:none; font-size:1px; color:#f2f2f7; line-height:1px; max-height:0; max-width:0; opacity:0; overflow:hidden;">
      {previa}
    </div>

    <table role="presentation" class="fin-bg" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f2f2f7;">
      <tr>
        <td align="center" style="padding:40px 16px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:520px;">
            <tr>
              <td align="center" style="padding-bottom:28px;">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td width="36" height="36" align="center" valign="middle" bgcolor="#5B6BD9" style="width:36px; height:36px; border-radius:10px; background-color:#5b6bd9; color:#ffffff; font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif; font-size:18px; font-weight:700; line-height:36px; text-align:center;">F</td>
                    <td style="padding-left:10px;">
                      <span class="fin-title" style="font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif; font-size:18px; font-weight:600; color:#1c1c1e; letter-spacing:-0.3px;">Fin</span>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <tr>
              <td class="fin-card" bgcolor="#ffffff" style="background-color:#ffffff; border:1px solid #e9e9ef; border-radius:20px; padding:44px 40px;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td class="fin-title" style="font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif; font-size:27px; font-weight:600; color:#1c1c1e; letter-spacing:-0.7px; line-height:1.2; padding-bottom:14px;">{titulo}</td>
                  </tr>

                  <tr>
                    <td class="fin-text" style="font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif; font-size:15px; color:#636366; line-height:1.6; padding-bottom:32px;">{texto}</td>
                  </tr>

                  <!-- O padding vive no <td>: um <a> sozinho perde area de clique no Outlook. -->
                  <tr>
                    <td style="padding-bottom:28px;">
                      <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                        <tr>
                          <td bgcolor="#1C1C1E" style="border-radius:999px; background-color:#1c1c1e;">
                            <a class="fin-button" href="{{{{ .ConfirmationURL }}}}" target="_blank" style="display:inline-block; padding:15px 34px; font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif; font-size:15px; font-weight:600; color:#ffffff; text-decoration:none; border-radius:999px;">{botao}</a>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>

                  <!-- Codigo, para quem abriu o e-mail em outro aparelho. -->
                  <tr>
                    <td class="fin-codebox" bgcolor="#f7f7fa" style="background-color:#f7f7fa; border:1px solid #e9e9ef; border-radius:12px; padding:18px 20px;">
                      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                        <tr>
                          <td class="fin-muted" style="font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif; font-size:12px; color:#8e8e93; padding-bottom:6px;">Ou use este código no app</td>
                        </tr>
                        <tr>
                          <td class="fin-code" style="font-family:'SF Mono','Segoe UI Mono',Consolas,monospace; font-size:24px; font-weight:600; color:#1c1c1e; letter-spacing:5px;">{{{{ .Token }}}}</td>
                        </tr>
                      </table>
                    </td>
                  </tr>

                  <tr>
                    <td class="fin-divider" style="border-top:1px solid #e9e9ef; padding-top:24px;">
                      <p class="fin-muted" style="margin:0 0 10px 0; font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif; font-size:13px; color:#8e8e93; line-height:1.6;">
                        {validade} Se o botão não funcionar, copie e cole este endereço no navegador:
                      </p>
                      <p style="margin:0;">
                        <a href="{{{{ .ConfirmationURL }}}}" target="_blank" style="font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif; font-size:12px; color:#5b6bd9; text-decoration:underline; word-break:break-all;">{{{{ .ConfirmationURL }}}}</a>
                      </p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <tr>
              <td align="center" style="padding-top:26px;">
                <p class="fin-footer" style="margin:0; font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif; font-size:12px; color:#8e8e93; line-height:1.6;">{rodape}</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


@dataclass(frozen=True)
class Template:
    arquivo: str
    local: str
    titulo: str
    titulo_arquivo: str
    previa: str
    texto: str
    botao: str
    validade: str
    rodape: str


EMAIL = "<strong style=\"font-weight:600;\">{{ .Email }}</strong>"

TEMPLATES = [
    Template(
        arquivo="confirmacao.html",
        local="Confirm signup",
        titulo="Confirme seu e-mail",
        titulo_arquivo="confirmação de e-mail",
        previa="Confirme seu endereço para ativar sua conta no Fin.",
        texto=(
            "Falta um passo para sua conta ficar pronta. Toque no botão abaixo e você "
            "já entra direto no app."
        ),
        botao="Confirmar e-mail",
        validade="O link vale por 24 horas.",
        rodape=(
            f"Você recebeu este e-mail porque alguém usou {EMAIL} para criar uma conta "
            "no Fin. Se não foi você, pode ignorar — sem a confirmação, a conta não é "
            "ativada."
        ),
    ),
    Template(
        arquivo="recuperar-senha.html",
        local="Reset password",
        titulo="Redefinir sua senha",
        titulo_arquivo="recuperação de senha",
        previa="Link para você criar uma nova senha no Fin.",
        texto=(
            "Recebemos um pedido para redefinir sua senha. Toque no botão abaixo para "
            "escolher uma nova."
        ),
        botao="Criar nova senha",
        validade="O link vale por 1 hora, por segurança.",
        rodape=(
            f"Este e-mail foi enviado para {EMAIL}. Se você não pediu para redefinir a "
            "senha, ignore — sua senha atual continua valendo e nada muda."
        ),
    ),
    Template(
        arquivo="link-magico.html",
        local="Magic Link",
        titulo="Seu link de acesso",
        titulo_arquivo="link mágico",
        previa="Entre no Fin sem digitar senha.",
        texto="Toque no botão abaixo para entrar na sua conta. Não precisa de senha.",
        botao="Entrar no Fin",
        validade="O link vale por 1 hora e só pode ser usado uma vez.",
        rodape=(
            f"Este e-mail foi enviado para {EMAIL}. Se você não pediu este acesso, "
            "ignore — ninguém entra sem tocar no link."
        ),
    ),
    Template(
        arquivo="trocar-email.html",
        local="Change Email Address",
        titulo="Confirme seu novo e-mail",
        titulo_arquivo="troca de e-mail",
        previa="Confirme o novo endereço da sua conta no Fin.",
        texto=(
            "Você pediu para trocar o e-mail da sua conta. Confirme o novo endereço "
            "para a mudança valer."
        ),
        botao="Confirmar novo e-mail",
        validade="O link vale por 24 horas.",
        rodape=(
            "Se você não pediu essa troca, ignore este e-mail e troque sua senha — o "
            "endereço antigo continua valendo até a confirmação."
        ),
    ),
]


def main() -> int:
    for template in TEMPLATES:
        html = SHELL.format(
            titulo=template.titulo,
            titulo_arquivo=template.titulo_arquivo,
            local=template.local,
            previa=template.previa,
            texto=template.texto,
            botao=template.botao,
            validade=template.validade,
            rodape=template.rodape,
        )
        destino = BASE_DIR / template.arquivo
        destino.write_text(html, encoding="utf-8")
        print(f"  {template.arquivo:24} -> painel: {template.local}")

    print(f"\n{len(TEMPLATES)} templates gerados em {BASE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
