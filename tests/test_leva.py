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


def test_data_invalida():
    dado = uma_leva()
    dado["data"] = "08/10/2026"
    with pytest.raises(ValueError, match="data invalida"):
        leva.validar(dado)


def test_forma_errada_vira_valueerror():
    for ruim in ([], "x", {"nome": "a", "slug": "a", "data": "2026-10-08", "roteiros": "x"},
                 uma_leva("texto"), uma_leva(["lista"])):
        with pytest.raises(ValueError):
            leva.validar(ruim)


def test_gravar_recusa_slug_diferente_da_pasta(tmp_path):
    with pytest.raises(ValueError, match="slug"):
        leva.gravar(uma_leva(), tmp_path / "outra")


def test_temas_entregues_tolerante(tmp_path):
    pasta = tmp_path / "ceci"
    leva.gravar(uma_leva(roteiro("r1", "Jaleco")), pasta)
    levas = pasta / "levas"
    (levas / "quebrada.json").write_text("{nao e json", encoding="utf-8")
    (levas / "lista.json").write_text("[]", encoding="utf-8")
    (levas / "rot-texto.json").write_text('{"roteiros": "x"}', encoding="utf-8")
    (levas / "rot-item.json").write_text('{"roteiros": ["x", 3]}', encoding="utf-8")
    assert leva.temas_entregues(pasta) == ["Jaleco"]


def test_travessao_em_referencias():
    r = roteiro()
    r["referencias"] = ["ok", "a " + chr(0x2013) + " b"]
    with pytest.raises(ValueError, match="travessao"):
        leva.validar(uma_leva(r))


def test_temas_entregues_inclui_rascunhos(tmp_path):
    pasta = tmp_path / "ceci"
    leva.gravar(uma_leva(roteiro("r1", "Jaleco")), pasta)
    rascunhos = pasta / "levas" / "rascunhos"
    rascunhos.mkdir()
    (rascunhos / "a.json").write_text(json.dumps(uma_leva(roteiro("r1", "Scrub"))), encoding="utf-8")
    (rascunhos / "quebrado.json").write_text("{nao", encoding="utf-8")
    assert leva.temas_entregues(pasta) == ["Jaleco", "Scrub"]


def test_temas_entregues_sem_repetir(tmp_path):
    pasta = tmp_path / "ceci"
    leva.gravar(uma_leva(roteiro("r1", "Jaleco"), roteiro("r2", "Scrub")), pasta)
    leva.gravar(uma_leva(roteiro("r1", "Jaleco")), pasta)
    assert leva.temas_entregues(pasta) == ["Jaleco", "Scrub"]


def test_fontes_precisa_ser_lista_de_textos():
    dado = uma_leva(dict(roteiro(), fontes="https://exemplo.com"))
    with pytest.raises(ValueError, match="fontes"):
        leva.validar(dado)
    leva.validar(uma_leva(dict(roteiro(), fontes=["https://exemplo.com"])))
