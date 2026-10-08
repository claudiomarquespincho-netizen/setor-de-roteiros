"""Plano B da coleta: ela cola os links dos reels em que fala."""

import json

import pytest

from scripts import coleta_links, transcricao

INFO = {
    "id": "DdMEgGcyLrb",
    "timestamp": 1757700251,
    "upload_date": "20250912",
    "duration": 133.4,
    "view_count": 92828,
    "url": "https://cdn.example/DdMEgGcyLrb.mp4",
    "description": " Ore pelo lugar que você trabalha. ",
}


def test_codigo_sai_do_link():
    assert coleta_links.codigo_do_link("https://www.instagram.com/reel/DdMEgGcyLrb/?igsh=x") == "DdMEgGcyLrb"
    assert coleta_links.codigo_do_link("https://instagram.com/p/AbC_d-1/") == "AbC_d-1"
    assert coleta_links.codigo_do_link("instagram.com/reels/XyZ123") == "XyZ123"


def test_link_que_nao_e_reel_e_recusado():
    with pytest.raises(ValueError, match="nao parece link de reel"):
        coleta_links.codigo_do_link("https://www.instagram.com/cicinavarro/")


def test_reel_tem_os_mesmos_campos_da_coleta():
    reel = coleta_links.reel_de(INFO, "https://www.instagram.com/reel/DdMEgGcyLrb/", "DdMEgGcyLrb")
    assert set(reel) == {"url", "codigo", "quando", "segundos", "views", "mp4", "legenda"}
    assert set(transcricao.CAMPOS_DO_REEL) <= set(reel)
    assert reel["codigo"] == "DdMEgGcyLrb"
    assert reel["quando"] == "2025-09-12"
    assert reel["segundos"] == 133
    assert reel["views"] == 92828
    assert reel["legenda"] == "Ore pelo lugar que você trabalha."


def test_reel_sem_views_nem_duracao_fica_com_zero():
    info = {"id": "x", "upload_date": "20250101"}
    reel = coleta_links.reel_de(info, "https://instagram.com/reel/x/", "x")
    assert reel["views"] == 0 and reel["segundos"] == 0 and reel["legenda"] == ""


def _baixador_falso(chamadas):
    def baixar(link, arquivo):
        chamadas.append((link, arquivo))
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_bytes(b"mp4")
        codigo = arquivo.stem
        return dict(INFO, id=codigo)
    return baixar


def test_main_baixa_e_grava_reels_json(tmp_path, monkeypatch):
    chamadas = []
    monkeypatch.setattr(coleta_links, "baixar", _baixador_falso(chamadas))
    links = ["https://www.instagram.com/reel/AAA111/", "https://www.instagram.com/reel/BBB222/"]
    assert coleta_links.main(["coleta_links", str(tmp_path)] + links) == 0
    reels = json.loads((tmp_path / "reels.json").read_text(encoding="utf-8"))
    assert [r["codigo"] for r in reels] == ["AAA111", "BBB222"]
    assert chamadas[0][1] == tmp_path / "mp4" / "AAA111.mp4"
    assert (tmp_path / "mp4" / "BBB222.mp4").exists()


def test_main_nao_sobrescreve_reels_json(tmp_path, monkeypatch, capsys):
    (tmp_path / "reels.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(coleta_links, "baixar", lambda *a: pytest.fail("nao devia baixar"))
    assert coleta_links.main(["coleta_links", str(tmp_path), "https://instagram.com/reel/A1/"]) == 1
    assert "--sobrescrever" in capsys.readouterr().out


def test_main_sobrescreve_com_flag(tmp_path, monkeypatch):
    (tmp_path / "reels.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(coleta_links, "baixar", _baixador_falso([]))
    assert coleta_links.main(["coleta_links", str(tmp_path), "https://instagram.com/reel/A1/",
                              "--sobrescrever"]) == 0
    assert len(json.loads((tmp_path / "reels.json").read_text(encoding="utf-8"))) == 1


def test_main_sem_link_mostra_uso(tmp_path, capsys):
    assert coleta_links.main(["coleta_links", str(tmp_path)]) == 1
    assert "uso" in capsys.readouterr().out


def test_main_diz_qual_link_falhou(tmp_path, monkeypatch, capsys):
    def falha(link, arquivo):
        raise RuntimeError("HTTP 404")
    monkeypatch.setattr(coleta_links, "baixar", falha)
    assert coleta_links.main(["coleta_links", str(tmp_path), "https://instagram.com/reel/ZZ9/"]) == 1
    assert "ZZ9" in capsys.readouterr().out
    assert not (tmp_path / "reels.json").exists()
