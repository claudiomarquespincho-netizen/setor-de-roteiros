"""Quem pode receber roteiro: os clientes do repo e os perfis desta maquina.

Cliente mora em clientes/<slug>/ e vai pro git. Perfil e' o "para voce" de
quem usa o repo, mora em perfis/<slug>/ e o git ignora. Os dois tem a mesma
forma, com retrato.json na raiz, e por isso o resto do repo nao distingue um
do outro.

Uso:
    python3 -m scripts.perfis           lista clientes e perfis em JSON
"""

import json
import pathlib
import re
import sys
import unicodedata

RAIZ = pathlib.Path(__file__).resolve().parents[1]
CLIENTES = RAIZ / "clientes"
PERFIS = RAIZ / "perfis"


def listar(pasta):
    achados = []
    for retrato in pathlib.Path(pasta).glob("*/retrato.json"):
        try:
            dado = json.loads(retrato.read_text(encoding="utf-8"))
        except ValueError:
            print(f"aviso: {retrato} nao e' JSON valido, ignorado", file=sys.stderr)
            continue
        if not isinstance(dado, dict):
            print(f"aviso: {retrato} nao e' um objeto JSON, ignorado", file=sys.stderr)
            continue
        achados.append({"slug": retrato.parent.name, "nome": dado.get("nome") or retrato.parent.name,
                        "pasta": str(retrato.parent)})
    return sorted(achados, key=lambda c: c["nome"].lower())


def slug_de(nome):
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")


def gravar_perfil(retrato, pasta=PERFIS, clientes=CLIENTES):
    if not retrato.get("nome"):
        raise ValueError("perfil sem nome")
    if not retrato.get("voz"):
        raise ValueError("perfil sem voz: sem a fala dela o roteiro sai generico")
    retrato = dict(retrato)
    retrato["slug"] = slug_de(retrato.get("slug") or retrato["nome"])
    if not retrato["slug"]:
        raise ValueError("perfil com slug vazio: use letras ou numeros no nome")
    if (pathlib.Path(clientes) / retrato["slug"]).exists():
        raise ValueError(f"ja existe um cliente com o slug {retrato['slug']}")
    destino = pathlib.Path(pasta) / retrato["slug"]
    destino.mkdir(parents=True, exist_ok=True)
    caminho = destino / "retrato.json"
    caminho.write_text(json.dumps(retrato, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return caminho


def main():
    print(json.dumps({"clientes": listar(CLIENTES), "perfis": listar(PERFIS)},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
