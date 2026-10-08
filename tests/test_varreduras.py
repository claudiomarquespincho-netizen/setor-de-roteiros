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


def test_codigos_de_saida(tmp_path, capsys):
    bom = _leva(tmp_path, [r("r1", "G1.", "C1.", "F1."), r("r2", "G2.", "C2.", "F2.")])
    mod = [varredura_vicios, varredura_repeticao, varredura_copia]
    for m in mod:
        assert m.main(["x", str(bom)]) == 0
        assert m.main(["x"]) == 2
        assert m.main(["x", str(tmp_path / "nao-existe.json")]) == 2
    ruim = tmp_path / "ruim.json"
    ruim.write_text("{nao", encoding="utf-8")
    for m in mod:
        assert m.main(["x", str(ruim)]) == 2
    assert "erro" in capsys.readouterr().err


def test_repeticao_reprova_sai_1(tmp_path):
    caminho = _leva(tmp_path, [r("r1", "G1.", "C1.", "Salva esse video agora."),
                               r("r2", "G2.", "C2.", "Salva esse video agora.")])
    assert varredura_repeticao.main(["x", str(caminho)]) == 1


def test_repeticao_sem_fala_sai_2(tmp_path):
    caminho = _leva(tmp_path, [r("r1", "G1.", "C1.", "F1.")])
    (leva.pasta_da_leva(caminho) / "transcricoes.md").unlink()
    assert varredura_repeticao.main(["x", str(caminho)]) == 2


def test_copia_reprova_sai_1_e_avisa_fonte_ausente(tmp_path, capsys):
    caminho = _leva(tmp_path, [r("r1", "G.", "eu sabia exatamente quanto tinha ficado na mesa ontem", "F.")])
    pasta = leva.pasta_da_leva(caminho)
    (pasta / "referencias").mkdir()
    (pasta / "referencias" / "x.md").write_text(
        "e eu sabia exatamente quanto tinha ficado na mesa", encoding="utf-8")
    (pasta / "transcricoes.md").unlink()
    assert varredura_copia.main(["x", str(caminho)]) == 1
    assert "aviso: fonte nao encontrada" in capsys.readouterr().out


def test_vicios_diz_quando_secao_esta_vazia(tmp_path, capsys):
    from scripts import varredura_vicios
    limpo = [{"chave": "r1", "gancho": "Um gancho so.", "corpo": "Corpo limpo aqui.",
              "fechamento": "Fecho."}]
    varredura_vicios.relatorio(limpo)
    saida = capsys.readouterr().out
    assert "== cauda de gancho ==\n  nenhuma" in saida
