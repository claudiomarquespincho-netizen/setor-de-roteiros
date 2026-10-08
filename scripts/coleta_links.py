"""Plano B da coleta: a pessoa cola os links dos reels em que ela fala.

Quando a Apify traz menos de 10 videos com fala, a voz sai rala. Aqui cada link
e' baixado pelo yt-dlp para <pasta>/mp4/<codigo>.mp4, e o reels.json sai com os
mesmos campos que a coleta grava, para a transcricao nao saber a diferenca.

Uso:
    python -m scripts.coleta_links <pasta> <link> [<link> ...] [--sobrescrever]
"""

import datetime
import json
import pathlib
import re
import sys

from scripts import coleta

PADRAO = re.compile(r"instagram\.com/(?:[^/]+/)?(?:reels?|p|tv)/([A-Za-z0-9_-]+)")


def codigo_do_link(link):
    achado = PADRAO.search(link)
    if not achado:
        raise ValueError(f"{link} nao parece link de reel do Instagram (instagram.com/reel/<codigo>)")
    return achado.group(1)


def baixar(link, arquivo):
    """Baixa um reel para `arquivo` e devolve o info do yt-dlp."""
    import yt_dlp
    arquivo = pathlib.Path(arquivo)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    opcoes = {
        "outtmpl": str(arquivo.with_suffix("")) + ".%(ext)s",
        "format": "mp4/bestvideo*+bestaudio/best",
        "merge_output_format": "mp4",
        "overwrites": True,
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        return ydl.extract_info(link, download=True)


def _quando(info):
    data = str(info.get("upload_date") or "")
    if re.fullmatch(r"\d{8}", data):
        return f"{data[:4]}-{data[4:6]}-{data[6:]}"
    if info.get("timestamp"):
        return datetime.datetime.fromtimestamp(
            int(info["timestamp"]), datetime.timezone.utc).strftime("%Y-%m-%d")
    return datetime.date.today().isoformat()


def reel_de(info, link, codigo):
    """O registro com os campos de coleta.normalizar."""
    try:
        segundos = int(round(float(info.get("duration") or 0)))
        views = int(info.get("view_count") or 0)
    except (TypeError, ValueError):
        segundos, views = 0, 0
    return {
        "url": link,
        "codigo": codigo,
        "quando": _quando(info),
        "segundos": segundos,
        "views": views,
        "mp4": info.get("url") or link,
        "legenda": (info.get("description") or "").strip(),
    }


def main(argv):
    argv = list(argv)
    sobrescrever = "--sobrescrever" in argv
    if sobrescrever:
        argv.remove("--sobrescrever")
    if len(argv) < 3:
        print("uso: python -m scripts.coleta_links <pasta> <link> [<link> ...] [--sobrescrever]")
        return 1
    pasta, links = pathlib.Path(argv[1]), argv[2:]
    if (pasta / "reels.json").exists() and not sobrescrever:
        print(f"{pasta / 'reels.json'} ja existe: passe --sobrescrever para trocar pelos links")
        return 1
    reels = []
    for link in links:
        try:
            codigo = codigo_do_link(link)
            info = baixar(link, pasta / "mp4" / f"{codigo}.mp4")
        except Exception as erro:                      # noqa: o motivo vem no texto
            print(f"nao baixei {link}: {erro}")
            return 1
        reels.append(reel_de(info or {}, link, codigo))
    reels.sort(key=lambda r: r["quando"], reverse=True)
    coleta.gravar(reels, pasta)
    print(f"{len(reels)} reels dos links em {pasta / 'reels.json'}, mp4 em {pasta / 'mp4'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
