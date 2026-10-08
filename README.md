# Setor de Roteiros

Roteiros de video curto, na voz de quem vai gravar, num Google Doc com uma aba
por roteiro.

## Antes de tudo

- Claude Code instalado e com login feito.
- git com acesso ao repositorio privado no GitHub (para clonar e para dar push).
- Homebrew, se o ffmpeg ainda nao estiver instalado.
- Uns 1,5 GB livres: o modelo do Whisper baixa na primeira transcricao.
- Mac com Apple Silicon recomendado (no Intel a transcricao e' bem mais lenta).

## Primeira vez

    git clone https://github.com/claudiomarquespincho-netizen/setor-de-roteiros.git
    cd setor-de-roteiros
    ./instalar.sh
    claude

O `./instalar.sh` cria um ambiente Python em `.venv/` dentro da pasta e instala
tudo nele. Dentro do Claude Code, digite `/comecar`.

## O que voce vai precisar

- Para fazer roteiros para voce mesma: o token da Apify da assessoria (peca a
  quem cuida do repo). Ele puxa seus reels para pegar o seu jeito de falar.
- Na primeira leva: login com a sua conta Google, para o Doc ir para o seu Drive.
  Seu e-mail precisa estar na lista de testadores do app (peca a quem cuida do repo).
