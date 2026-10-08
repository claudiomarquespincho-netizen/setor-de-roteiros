import json

import pytest

from scripts import leva


def roteiro(chave="r1", tema="Jaleco"):
    return {"chave": chave, "tema": tema, "gancho": "Gancho.", "corpo": "Corpo.",
            "fechamento": "Fecho."}


def uma_leva(*roteiros):
    return {"nome": "Cici", "slug": "ceci", "data": "2026-10-08", "doc_url": "",
            "roteiros": list(roteiros) or [roteiro()]}


def test_leva_valida_passa():
    leva.validar(uma_leva())


def test_falta_campo_obrigatorio():
    r = roteiro()
    del r["gancho"]
    with pytest.raises(ValueError, match="r1 sem gancho"):
        leva.validar(uma_leva(r))


def test_mais_de_cinco_roteiros():
    rs = [roteiro(f"r{i}", f"tema {i}") for i in range(1, 7)]
    with pytest.raises(ValueError, match="de 1 a 5"):
        leva.validar(uma_leva(*rs))


def test_chave_repetida():
    with pytest.raises(ValueError, match="chave repetida"):
        leva.validar(uma_leva(roteiro("r1"), roteiro("r1", "outro")))


def test_travessao_reprova():
    r = roteiro()
    r["corpo"] = "Isso " + chr(0x2014) + " aquilo."
    with pytest.raises(ValueError, match="travessao"):
        leva.validar(uma_leva(r))


def test_gravar_ler_e_pasta(tmp_path):
    pasta = tmp_path / "clientes" / "ceci"
    caminho = leva.gravar(uma_leva(), pasta)
    assert caminho == pasta / "levas" / "2026-10-08.json"
    assert leva.ler(caminho)["nome"] == "Cici"
    assert leva.pasta_da_leva(caminho) == pasta


def test_gravar_nao_sobrescreve(tmp_path):
    pasta = tmp_path / "ceci"
    leva.gravar(uma_leva(), pasta)
    segundo = leva.gravar(uma_leva(), pasta)
    assert segundo.name == "2026-10-08-2.json"


def test_temas_entregues(tmp_path):
    pasta = tmp_path / "ceci"
    leva.gravar(uma_leva(roteiro("r1", "Jaleco"), roteiro("r2", "Scrub")), pasta)
    assert leva.temas_entregues(pasta) == ["Jaleco", "Scrub"]
    assert leva.temas_entregues(tmp_path / "vazio") == []
