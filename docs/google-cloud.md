# Setup do Google Cloud (uma vez, por quem cuida do repo)

Sem isso o Doc em abas nao sai. Leva uns 10 minutos.

1. Abra https://console.cloud.google.com e crie um projeto chamado "Setor de Roteiros".
2. Em "APIs e servicos", ative a **Google Docs API** e a **Google Drive API**.
3. Em "Tela de consentimento OAuth": tipo **Externo**, status **Em teste**. Nome do
   app "Setor de Roteiros". Em "Usuarios de teste", adicione o e-mail Google de cada
   pessoa do time.
4. Em "Credenciais", crie um **ID do cliente OAuth** do tipo **App para computador**.
5. Baixe o JSON e salve como `config/google-client.json` neste repo.
6. Commite esse arquivo. O repo e' privado, e para app de computador o Google nao
   trata esse segredo como confidencial.

Pessoa nova no time: adicione o e-mail dela em "Usuarios de teste" antes da primeira
leva, ou o login dela vai dar "acesso bloqueado".

Em modo de teste o login vale 7 dias: o Google faz o refresh token expirar nesse prazo
para todo app que pede escopo alem de nome, e-mail e perfil, e Docs e Drive entram
nessa regra (developers.google.com/identity/protocols/oauth2). Quando expirar, o
`/comecar` pede o login de novo.
