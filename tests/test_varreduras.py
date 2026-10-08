import json
import pathlib

from scripts import leva, varredura_copia, varredura_repeticao, varredura_vicios


def _leva(tmp_path, roteiros):
    pasta = tmp_path / "clientes" / "fulana"
    pasta.mkdir(parents=True)
    (pasta / "transcricoes.md").write_text("gente eu acho que isso e assim mesmo", encoding="utf-8")
    dado = {"nome": "Fulana", "slug": "fulana", "data": "2026-10-08", "doc_url": "",
            "roteiros": roteiros}
    return leva.gravar(dado, pasta)


def r(chave, gancho, corpo, fecho):
    return {"chave": chave, "tema": chave, "gancho": gancho, "corpo": corpo, "fechamento": fecho}


def test_vicios_le_leva_json(tmp_path):
    caminho = _leva(tmp_path, [r("r1", "Gancho.", "Isso vai te surpreender muito.", "Fim um.")])
    roteiros = varredura_vicios.carregar(caminho)
    achados = list(varredura_vicios.por_expressao(roteiros))
    assert any(v == "diz como se sentir" for v, _, _ in achados)


def test_repeticao_acha_fala_da_pasta(tmp_path):
    caminho = _leva(tmp_path, [r("r1", "G1.", "C1.", "F1.")])
    fontes = varredura_repeticao.fala_do_cliente(leva.pasta_da_leva(caminho))
    assert fontes[0].name == "transcricoes.md"


def test_repeticao_reprova_fecho_igual(tmp_path):
    caminho = _leva(tmp_path, [r("r1", "G1.", "C1.", "Salva esse video agora."),
                               r("r2", "G2.", "C2.", "Salva esse video agora.")])
    dado = leva.ler(caminho)
    reprova, _ = varredura_repeticao.varrer(
        dado["roteiros"], varredura_repeticao.fala_do_cliente(leva.pasta_da_leva(caminho)))
    assert any(t == "fechamento repetido" for t, _ in reprova)


def test_copia_pega_frase_de_referencia(tmp_path):
    caminho = _leva(tmp_path, [r("r1", "G.", "eu sabia exatamente quanto tinha ficado na mesa ontem", "F.")])
    pasta = leva.pasta_da_leva(caminho)
    (pasta / "referencias").mkdir()
    (pasta / "referencias" / "x.md").write_text(
        "e eu sabia exatamente quanto tinha ficado na mesa", encoding="utf-8")
    fontes = {"referencia": varredura_copia.referencias(pasta),
              "publicado": varredura_copia.publicados(pasta)}
    achados = varredura_copia.varrer(leva.ler(caminho)["roteiros"], fontes)
    assert achados and achados[0][1] == "referencia"
