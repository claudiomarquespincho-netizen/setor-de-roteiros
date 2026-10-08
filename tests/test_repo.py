"""O que o repo promete em volta do codigo: perfil nao vai pro git, cliente e' valido."""

import json
import pathlib
import subprocess

RAIZ = pathlib.Path(__file__).resolve().parents[1]
TRAVESSOES = (chr(0x2014), chr(0x2013))


def _ignorado(caminho):
    r = subprocess.run(["git", "check-ignore", "-q", caminho], cwd=RAIZ)
    return r.returncode == 0


def test_perfil_nao_vai_pro_git():
    assert _ignorado("perfis/fulana/retrato.json")
    assert _ignorado("perfis/fulana/levas/2026-10-08.json")


def test_video_nao_vai_pro_git():
    assert _ignorado("clientes/ceci/mp4/abc.mp4")
    assert _ignorado("clientes/felipe/extras/yt.m4a")


def test_todo_cliente_tem_nome_e_slug_da_pasta():
    for retrato in sorted((RAIZ / "clientes").glob("*/retrato.json")):
        dado = json.loads(retrato.read_text(encoding="utf-8"))
        assert dado.get("nome"), f"{retrato} sem nome"
        assert dado.get("slug") == retrato.parent.name, f"{retrato}: slug diferente da pasta"


def test_texto_novo_sem_travessao():
    pastas = ["scripts", ".claude", "docs"]
    arquivos = [RAIZ / "CLAUDE.md", RAIZ / "README.md"]
    for p in pastas:
        arquivos += [a for a in (RAIZ / p).rglob("*") if a.suffix in (".py", ".md")]
    for a in arquivos:
        if a.exists():
            texto = a.read_text(encoding="utf-8")
            assert not any(t in texto for t in TRAVESSOES), f"travessao em {a}"
