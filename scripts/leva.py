"""A leva em JSON: o formato que o /comecar grava e que varredura e Doc leem.

Uma leva mora em <pasta>/levas/<data>.json, e <pasta> e' clientes/<slug> ou
perfis/<slug>. A pasta sai do caminho, e por isso nenhuma peca precisa de flag
dizendo de quem e' a leva.
"""

import json
import pathlib
import re

OBRIGATORIOS = ("chave", "tema", "gancho", "corpo", "fechamento")
TEXTOS = ("tema", "titulo", "gravacao", "gancho", "corpo", "fechamento")
TRAVESSOES = (chr(0x2014), chr(0x2013))
MAXIMO = 5


def _texto_com_travessao(valor):
    return isinstance(valor, str) and any(t in valor for t in TRAVESSOES)


def validar(dado):
    if not isinstance(dado, dict):
        raise ValueError("a leva precisa ser um objeto JSON")
    problemas = []
    for campo in ("nome", "slug", "data"):
        if not dado.get(campo):
            problemas.append(f"leva sem {campo}")
    if dado.get("data") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(dado["data"])):
        problemas.append("data invalida: use AAAA-MM-DD")
    roteiros = dado.get("roteiros") or []
    if not isinstance(roteiros, list):
        raise ValueError("roteiros precisa ser uma lista")
    if not all(isinstance(r, dict) for r in roteiros):
        raise ValueError("cada roteiro precisa ser um objeto")
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
            if _texto_com_travessao(r.get(campo)):
                problemas.append(f"{chave}: travessao em {campo}")
        refs = r.get("referencias")
        if isinstance(refs, list) and any(_texto_com_travessao(x) for x in refs):
            problemas.append(f"{chave}: travessao em referencias")
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
    if dado["slug"] != pathlib.Path(pasta).name:
        raise ValueError(f"slug da leva ({dado['slug']}) difere da pasta ({pathlib.Path(pasta).name})")
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
    """Temas ja mostrados ao cliente, inclusive os de levas/rascunhos/: tema visto nunca volta."""
    temas = []
    levas = pathlib.Path(pasta) / "levas"
    for arquivo in sorted(levas.glob("*.json")) + sorted((levas / "rascunhos").glob("*.json")):
        try:
            dado = json.loads(arquivo.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(dado, dict) or not isinstance(dado.get("roteiros"), list):
            continue
        temas += [r["tema"] for r in dado["roteiros"] if isinstance(r, dict) and r.get("tema")]
    return temas
