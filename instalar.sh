#!/usr/bin/env bash
# Instala o que o setor de roteiros usa e confere se esta tudo de pe.
set -euo pipefail
cd "$(dirname "$0")"

command -v python3 >/dev/null || { echo "Instale antes: python3"; exit 1; }

# ffmpeg vem do brew, e o brew so' e' exigido se o ffmpeg faltar.
# yt-dlp vem do pip (requirements.txt) e roda como .venv/bin/python -m yt_dlp.
if ! command -v ffmpeg >/dev/null; then
  command -v brew >/dev/null || { echo "Instale antes: ffmpeg, ou o brew (https://brew.sh) para eu instalar"; exit 1; }
  brew install ffmpeg
fi

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv || {
    echo "Nao consegui criar o ambiente .venv. Instale o Python de python.org e rode ./instalar.sh de novo."
    exit 1
  }
fi
PY=.venv/bin/python

"$PY" -m pip install -q --upgrade pip >/dev/null 2>&1 || true
"$PY" -m pip install -q -r requirements.txt || {
  echo "A instalacao dos pacotes falhou (veja a mensagem acima). Confira a internet e rode ./instalar.sh de novo; se repetir, mande a mensagem para quem cuida do repo."
  exit 1
}

mkdir -p "$HOME/.config/setor-de-roteiros"

"$PY" -m pytest -q

echo
[ -f "$HOME/.config/setor-de-roteiros/apify.env" ] && echo "apify: ok" || echo "apify: sem token (so precisa para roteiros para voce)"
[ -f config/google-client.json ] && echo "google: app configurado" || echo "google: falta config/google-client.json (docs/google-cloud.md)"
echo
echo "Pronto. Abra o Claude Code nesta pasta e digite /comecar"
