import json

import pytest

from scripts import perfis


def _retrato(pasta, slug, nome):
    (pasta / slug).mkdir(parents=True)
    (pasta / slug / "retrato.json").write_text(
        json.dumps({"nome": nome, "slug": slug, "voz": "x"}), encoding="utf-8")


def test_lista_por_nome_de_exibicao(tmp_path):
    _retrato(tmp_path, "ceci", "Cici")
    _retrato(tmp_path, "dani", "Dani Facchinetti")
    nomes = [c["nome"] for c in perfis.listar(tmp_path)]
    assert nomes == ["Cici", "Dani Facchinetti"]


def test_pasta_sem_retrato_fica_fora(tmp_path):
    (tmp_path / "solta").mkdir()
    assert perfis.listar(tmp_path) == []


def test_slug():
    assert perfis.slug_de("Júlia Bressane") == "julia-bressane"
    assert perfis.slug_de("@cici.navarro") == "cici-navarro"


def test_gravar_perfil(tmp_path):
    caminho = perfis.gravar_perfil({"nome": "Fulana", "voz": "fala rapido"}, tmp_path)
    dado = json.loads(caminho.read_text(encoding="utf-8"))
    assert caminho == tmp_path / "fulana" / "retrato.json"
    assert dado["slug"] == "fulana"


def test_perfil_sem_voz_recusa(tmp_path):
    with pytest.raises(ValueError, match="voz"):
        perfis.gravar_perfil({"nome": "Fulana"}, tmp_path)


def test_slug_passa_por_slug_de(tmp_path):
    caminho = perfis.gravar_perfil({"nome": "X", "slug": "Ana Lu!", "voz": "v"}, tmp_path, clientes=tmp_path / "c")
    assert caminho.parent.name == "ana-lu"
    assert json.loads(caminho.read_text(encoding="utf-8"))["slug"] == "ana-lu"


def test_slug_vazio_recusa(tmp_path):
    with pytest.raises(ValueError, match="slug"):
        perfis.gravar_perfil({"nome": "!!!", "voz": "v"}, tmp_path, clientes=tmp_path / "c")


def test_slug_de_cliente_existente_recusa(tmp_path):
    clientes = tmp_path / "clientes"
    _retrato(clientes, "ceci", "Cici")
    with pytest.raises(ValueError, match="cliente"):
        perfis.gravar_perfil({"nome": "Ceci", "voz": "v"}, tmp_path / "perfis", clientes=clientes)


def test_regravar_perfil_existente_pode(tmp_path):
    perfis.gravar_perfil({"nome": "Fulana", "voz": "a"}, tmp_path, clientes=tmp_path / "c")
    caminho = perfis.gravar_perfil({"nome": "Fulana", "voz": "b"}, tmp_path, clientes=tmp_path / "c")
    assert json.loads(caminho.read_text(encoding="utf-8"))["voz"] == "b"


def test_listar_nome_vazio_usa_pasta(tmp_path):
    (tmp_path / "zeca").mkdir()
    (tmp_path / "zeca" / "retrato.json").write_text(json.dumps({"nome": ""}), encoding="utf-8")
    assert perfis.listar(tmp_path)[0]["nome"] == "zeca"


def test_listar_json_quebrado_pula_e_avisa(tmp_path, capsys):
    _retrato(tmp_path, "ok", "Ok")
    (tmp_path / "ruim").mkdir()
    (tmp_path / "ruim" / "retrato.json").write_text("{quebrado", encoding="utf-8")
    assert [c["slug"] for c in perfis.listar(tmp_path)] == ["ok"]
    assert "ruim" in capsys.readouterr().err
