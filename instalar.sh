#!/usr/bin/env bash
# Instala o que o setor de roteiros usa e confere se esta tudo de pe.
set -euo pipefail
cd "$(dirname "$0")"

command -v python3 >/dev/null || { echo "Instale antes: python3"; exit 1; }

# ffmpeg vem do brew, e o brew so' e' exigido se o ffmpeg faltar.
# yt-dlp vem do pip (requirements.txt) e roda como python3 -m yt_dlp.
if ! command -v ffmpeg >/dev/null; then
  command -v brew >/dev/null || { echo "Instale antes: ffmpeg, ou o brew (https://brew.sh) para eu instalar"; exit 1; }
  brew install ffmpeg
fi

python3 -m pip install -q -r requirements.txt

mkdir -p "$HOME/.config/setor-de-roteiros"

python3 -m pytest -q

echo
[ -f "$HOME/.config/setor-de-roteiros/apify.env" ] && echo "apify: ok" || echo "apify: sem token (so precisa para roteiros para voce)"
[ -f config/google-client.json ] && echo "google: app configurado" || echo "google: falta config/google-client.json (docs/google-cloud.md)"
echo
echo "Pronto. Abra o Claude Code nesta pasta e digite /comecar"
