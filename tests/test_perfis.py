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
