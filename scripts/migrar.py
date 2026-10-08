"""Traz do acervoroteiros o que o time precisa para escrever. Roda uma vez.

O acervoroteiros e' a bancada: la se testa, aqui se usa. Este script copia a
base, as transcricoes dos criadores de referencia, os clientes ativos e as
levas que ja foram entregues, para a trava de nao repetir tema saber o que
cada cliente ja recebeu. Video nao vem: o retrato e a transcricao bastam.

Uso:
    python3 -m scripts.migrar <caminho do acervoroteiros>
"""

import importlib.util
import json
import pathlib
import re
import shutil
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[1]
FORA = {"luiz"}
DO_CLIENTE = ("retrato.json", "regras.md", "grade-do-mes.md")
DA_COLETA = ("transcricoes.md", "reels.json")
CAMPOS_DA_LEVA = ("chave", "tema", "titulo", "molde", "gravacao", "gancho", "corpo",
                  "fechamento", "referencias", "tipo")


def familia_e_versao(stem):
    """'2026-09-18-dez-v2' -> ('dez', 2). Sem marcador (ou -a-mao, -de-teste) e' a versao 1."""
    nome = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)
    achou = re.search(r"-v(\d+)$", nome)
    if achou:
        return nome[:achou.start()], int(achou.group(1))
    for marca in ("-a-mao", "-de-teste"):
        if nome.endswith(marca):
            return nome[:-len(marca)], 1
    return nome, 1


def separar_versoes(stems):
    """Devolve (ficam, rascunhos): de cada familia de versoes, so a ultima fica."""
    familias = {}
    for stem in stems:
        familia, versao = familia_e_versao(stem)
        familias.setdefault(familia, []).append((versao, stem))
    ficam, rascunhos = [], []
    for itens in familias.values():
        itens.sort()
        ficam.append(itens[-1][1])
        rascunhos.extend(stem for _, stem in itens[:-1])
    return ficam, rascunhos


def transcricoes_do_felipe(legendas, alvo):
    partes = ["# Transcricoes do Felipe (so a fala dele)\n"]
    for nome in ("felipe-pare-de-correr-atras-do-dinheiro", "felipe-quero-construir-algo-que-faca-sentido"):
        texto = (legendas / f"{nome}.txt").read_text(encoding="utf-8").strip()
        partes.append(f"\n## {nome.replace('felipe-', '').replace('-', ' ')}\n\n{texto}\n")
    alvo.write_text("".join(partes), encoding="utf-8")


def leva_do_ensaio(ensaio, nome, slug):
    spec = importlib.util.spec_from_file_location("ensaio_migrado", ensaio)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    roteiros = getattr(modulo, "ROTEIROS", None)
    if not roteiros:
        return None
    titulos = getattr(modulo, "TITULOS", {})
    limpos = []
    for r in roteiros:
        limpo = {k: r[k] for k in CAMPOS_DA_LEVA if r.get(k)}
        if r.get("chave") in titulos:
            limpo["titulo"] = titulos[r["chave"]]
        limpos.append(limpo)
    return {"nome": nome, "slug": slug, "data": ensaio.name[:10], "doc_url": "",
            "migrada_de": ensaio.name, "roteiros": limpos}


def copiar_cliente(origem, destino):
    destino.mkdir(parents=True, exist_ok=True)
    for nome in DO_CLIENTE:
        if (origem / nome).exists():
            shutil.copy2(origem / nome, destino / nome)
    coleta = origem / "coleta"
    if not coleta.exists():
        return
    for nome in DA_COLETA:
        if (coleta / nome).exists():
            shutil.copy2(coleta / nome, destino / nome)
    for arquivo in coleta.rglob("*"):
        relativo = arquivo.relative_to(coleta)
        if (arquivo.is_dir() or arquivo.suffix not in (".md", ".json")
                or relativo.parts[0] in ("mp4", "txt") or str(relativo) in DA_COLETA):
            continue
        alvo = destino / "extras" / relativo
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(arquivo, alvo)


def migrar_felipe(origem, destino):
    legendas = origem / "coleta" / "2026-09-29" / "legendas"
    extras = destino / "extras" / "2026-09-29" / "legendas"
    extras.mkdir(parents=True, exist_ok=True)
    for txt in legendas.glob("*.txt"):
        shutil.copy2(txt, extras / txt.name)
    transcricoes_do_felipe(legendas, destino / "transcricoes.md")
    (destino / "referencias").mkdir(exist_ok=True)
    for txt in legendas.glob("alfredo-*.txt"):
        shutil.copy2(txt, destino / "referencias" / f"{txt.stem}.md")


def migrar_levas(origem, destino, nome, slug):
    feitas = []
    gerados = {}
    for ensaio in sorted((origem / "ensaios").glob("*.py")):
        try:
            dado = leva_do_ensaio(ensaio, nome, slug)
        except Exception as erro:
            print(f"  pulei {ensaio.name}: {erro}")
            continue
        if dado is None:
            continue
        gerados[ensaio.stem] = dado
    ficam, rascunhos = separar_versoes(list(gerados))
    for pasta, stems in (("levas", ficam), ("levas/rascunhos", rascunhos)):
        for stem in stems:
            alvo = destino / pasta / f"{stem}.json"
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_text(json.dumps(gerados[stem], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return sorted(ficam), sorted(rascunhos)


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 1
    ar = pathlib.Path(argv[1])
    e2 = ar / "esteira2"

    (RAIZ / "base").mkdir(exist_ok=True)
    for nome in ("ganchos-1005.json", "vicios.md", "roteiros-referencia.md"):
        shutil.copy2(e2 / "base" / nome, RAIZ / "base" / nome)
    shutil.copy2(e2 / "regras" / "todos.md", RAIZ / "base" / "regras-gerais.md")

    for t in sorted(list((e2 / "referencias").glob("*/transcricoes.md"))
                    + list((e2 / "referencias").glob("*/raio-x.md"))):
        alvo = RAIZ / "referencias" / t.parent.name / t.name
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(t, alvo)

    for pasta in sorted((e2 / "clientes").iterdir()):
        if not (pasta / "retrato.json").exists() or pasta.name in FORA:
            continue
        nome = json.loads((pasta / "retrato.json").read_text(encoding="utf-8"))["nome"]
        destino = RAIZ / "clientes" / pasta.name
        copiar_cliente(pasta, destino)
        shutil.rmtree(destino / "levas", ignore_errors=True)
        levas, rascunhos = migrar_levas(pasta, destino, nome, pasta.name)
        print(f"{nome}: {len(levas)} leva(s), {len(rascunhos)} rascunho(s)")
        for r in rascunhos:
            print(f"  rascunho: {r}")
        if pasta.name == "felipe":
            migrar_felipe(pasta, destino)

    refs = ar / "docs" / "referencias-da-pessoa"
    cici = RAIZ / "clientes" / "ceci"
    for sub, nomes in (("fala", ["reels-que-a-cici-mandou-2026-09-18.md"]),
                       ("referencias", ["reels-que-a-cici-mandou-2026-09-18.md",
                                        "refs-transcritas-2026-09-24.md"])):
        for nome in nomes:
            if (refs / nome).exists():
                (cici / sub).mkdir(parents=True, exist_ok=True)
                shutil.copy2(refs / nome, cici / sub / nome)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
