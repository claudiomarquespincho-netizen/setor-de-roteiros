"""A leva em JSON: o formato que o /comecar grava e que varredura e Doc leem.

Uma leva mora em <pasta>/levas/<data>.json, e <pasta> e' clientes/<slug> ou
perfis/<slug>. A pasta sai do caminho, e por isso nenhuma peca precisa de flag
dizendo de quem e' a leva.
"""

import json
import pathlib

OBRIGATORIOS = ("chave", "tema", "gancho", "corpo", "fechamento")
TEXTOS = ("tema", "titulo", "gravacao", "gancho", "corpo", "fechamento")
TRAVESSOES = (chr(0x2014), chr(0x2013))
MAXIMO = 5


def validar(dado):
    problemas = []
    for campo in ("nome", "slug", "data"):
        if not dado.get(campo):
            problemas.append(f"leva sem {campo}")
    roteiros = dado.get("roteiros") or []
    if not 1 <= len(roteiros) <= MAXIMO:
        problemas.append(f"a leva tem {len(roteiros)} roteiros, e o limite e' de 1 a {MAXIMO}")
    vistas = set()
    for i, r in enumerate(roteiros, 1):
        chave = r.get("chave") or f"roteiro {i}"
        for campo in OBRIGATORIOS:
            if not r.get(campo):
                problemas.append(f"{chave} sem {campo}")
        if chave in vistas:
            problemas.append(f"chave repetida: {chave}")
        vistas.add(chave)
        for campo in TEXTOS:
            if any(t in (r.get(campo) or "") for t in TRAVESSOES):
                problemas.append(f"{chave}: travessao em {campo}")
    if problemas:
        raise ValueError("; ".join(problemas))


def ler(caminho):
    dado = json.loads(pathlib.Path(caminho).read_text(encoding="utf-8"))
    validar(dado)
    return dado


def pasta_da_leva(caminho):
    caminho = pathlib.Path(caminho).resolve()
    if caminho.parent.name != "levas":
        raise ValueError(f"a leva {caminho} precisa morar em <pasta>/levas/")
    return caminho.parent.parent


def gravar(dado, pasta):
    validar(dado)
    destino = pathlib.Path(pasta) / "levas"
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / f"{dado['data']}.json"
    n = 2
    while caminho.exists():
        caminho = destino / f"{dado['data']}-{n}.json"
        n += 1
    caminho.write_text(json.dumps(dado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return caminho


def atualizar(caminho, dado):
    """Regrava a leva no mesmo arquivo, por exemplo para guardar o doc_url."""
    validar(dado)
    pathlib.Path(caminho).write_text(
        json.dumps(dado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def temas_entregues(pasta):
    temas = []
    for arquivo in sorted((pathlib.Path(pasta) / "levas").glob("*.json")):
        dado = json.loads(arquivo.read_text(encoding="utf-8"))
        temas += [r["tema"] for r in dado.get("roteiros", []) if r.get("tema")]
    return temas
